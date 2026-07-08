#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import serial
import json
import math
import threading
import time
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster


def euler_to_quaternion(roll, pitch, yaw):
    qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
    qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
    qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    return [qx, qy, qz, qw]


class UnifiedUgvNode(Node):
    def __init__(self):
        super().__init__('unified_ugv_node')

        # --- Parametry (kalibracja bez rebuildu: --ros-args -p nazwa:=wartosc) ---
        self.declare_parameter('serial_port', '/dev/ttyCH343USB0')
        self.declare_parameter('baudrate', 115200)
        # Rozstaw kol. Firmware UGV02 (mainType==2) uzywa TRACK_WIDTH=0.172 m.
        # Skid-steer 6x4 slizga sie na skrecie -> efektywny rozstaw bywa WIEKSZY.
        # Robot na mapie skreca za malo/za duzo -> koryguj TEN parametr.
        self.declare_parameter('track_width', 0.172)
        # Skala enkodera: z testu 1 obrotu -> 0.251 m / 24 jedn. = 0.0105 m/jedn.
        # Zmierzone zgrubnie (+-1 jedn. ~ +-4%). Robot jedzie za daleko/za blisko
        # w LINII PROSTEJ -> koryguj TEN parametr.
        self.declare_parameter('meters_per_tick', 0.0105)
        # Max realny przyrost licznika na 1 ramce (odrzucanie glitchy / wrap-around).
        self.declare_parameter('max_tick_delta', 100)

        self.serial_port = self.get_parameter('serial_port').value
        baudrate = self.get_parameter('baudrate').value
        self.track_width = self.get_parameter('track_width').value
        self.mpt = self.get_parameter('meters_per_tick').value
        self.max_tick_delta = self.get_parameter('max_tick_delta').value

        # --- Stan odometrii ---
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        self.odl_prev = None
        self.odr_prev = None

        # --- Port szeregowy ---
        try:
            self.ser = serial.Serial(self.serial_port, baudrate, timeout=1)
            # ESP32 resetuje sie przy otwarciu portu CH343 (DTR/RTS -> EN).
            # Przez ~2 s bootuje i gubi komendy -> czekamy przed pierwsza komenda.
            time.sleep(2.0)
            self.ser.reset_input_buffer()
            self.get_logger().info(f"Polaczono z ESP32 na porcie: {self.serial_port}")
        except Exception as e:
            self.get_logger().error(f"Blad otwarcia portu szeregowego: {e}")
            raise e

        # --- ROS I/O ---
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)

        # Feedback WYLACZONY domyslnie (baseFeedbackFlow=0). Wlaczamy strumien
        # T:1001 i ponawiamy co 5 s (przezywa reset ESP32).
        self.enable_feedback_stream()
        self.create_timer(5.0, self.enable_feedback_stream)

        # --- Watek odczytu UART ---
        self.running = True
        self.read_thread = threading.Thread(target=self.uart_receive_loop, daemon=True)
        self.read_thread.start()

    def _send(self, obj):
        try:
            self.ser.write((json.dumps(obj) + "\n").encode('utf-8'))
        except Exception as e:
            self.get_logger().warn(f"Nie udalo sie wyslac przez UART: {e}")

    def enable_feedback_stream(self):
        # CMD_BASE_FEEDBACK_FLOW = 131, cmd=1 -> ciagly strumien ramek T:1001
        self._send({'T': 131, 'cmd': 1})

    def cmd_vel_callback(self, msg):
        linear_velocity = msg.linear.x
        angular_velocity = msg.angular.z

        # Filtr progowy dla malych predkosci obrotowych (z kodu Waveshare)
        if linear_velocity == 0:
            if 0 < angular_velocity < 0.2:
                angular_velocity = 0.2
            elif -0.2 < angular_velocity < 0:
                angular_velocity = -0.2

        # T:13 = CMD_ROS_CTRL (int). X=liniowa [m/s], Z=katowa [rad/s]
        self._send({'T': 13, 'X': linear_velocity, 'Z': angular_velocity})

    def uart_receive_loop(self):
        while self.running and rclpy.ok():
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    data = json.loads(line)
                    if data.get("T") == 1001:   # FEEDBACK_BASE_INFO
                        self.update_and_publish_odometry(data)
            except json.JSONDecodeError:
                pass  # niepelna ramka szeregowa
            except Exception as e:
                if self.running:
                    self.get_logger().warn(f"Blad w petli UART: {e}")

    def update_and_publish_odometry(self, data):
        # Enkodery to LICZNIKI AKUMULOWANE (odl=lewy, odr=prawy). Liczymy przyrost.
        try:
            odl = int(data["odl"])
            odr = int(data["odr"])
        except (KeyError, ValueError, TypeError):
            return

        current_time = self.get_clock().now()

        # Pierwsza ramka: tylko zapamietaj punkt odniesienia
        if self.odl_prev is None:
            self.odl_prev = odl
            self.odr_prev = odr
            return

        delta_l_ticks = odl - self.odl_prev
        delta_r_ticks = odr - self.odr_prev

        # Odrzuc glitche / wrap-around licznika (nierealny skok w jednej ramce)
        if abs(delta_l_ticks) > self.max_tick_delta or abs(delta_r_ticks) > self.max_tick_delta:
            self.odl_prev = odl
            self.odr_prev = odr
            return

        self.odl_prev = odl
        self.odr_prev = odr

        # Przyrosty dystansu kol [m]. Znak: przod = licznik rosnie -> dodatni dystans.
        d_left = delta_l_ticks * self.mpt
        d_right = delta_r_ticks * self.mpt

        # Kinematyka rozniczkowa
        d_center = (d_left + d_right) / 2.0
        d_theta = (d_right - d_left) / self.track_width

        # Integracja pozycji (metoda punktu srodkowego - dokladniejsza na luku)
        self.x += d_center * math.cos(self.th + d_theta / 2.0)
        self.y += d_center * math.sin(self.th + d_theta / 2.0)
        self.th += d_theta
        self.th = math.atan2(math.sin(self.th), math.cos(self.th))  # normalizacja (-pi, pi]

        # Predkosc do twist: z realnego pomiaru L/R (m/s), nie z rozniczkowania licznika
        v_left = float(data.get("L", 0.0))
        v_right = float(data.get("R", 0.0))
        v = (v_right + v_left) / 2.0
        w = (v_right - v_left) / self.track_width

        q = euler_to_quaternion(0, 0, self.th)
        stamp = current_time.to_msg()

        # 1. TF: odom -> base_link
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]
        self.tf_broadcaster.sendTransform(t)

        # 2. Odometry na /odom
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.x = q[0]
        odom.pose.pose.orientation.y = q[1]
        odom.pose.pose.orientation.z = q[2]
        odom.pose.pose.orientation.w = q[3]
        odom.twist.twist.linear.x = v
        odom.twist.twist.angular.z = w

        # Kowariancje (diagonala) - wymagane przez Nav2/EKF
        odom.pose.covariance[0] = 0.01    # x
        odom.pose.covariance[7] = 0.01    # y
        odom.pose.covariance[35] = 0.05   # yaw
        odom.twist.covariance[0] = 0.01   # vx
        odom.twist.covariance[35] = 0.05  # wz
        self.odom_pub.publish(odom)

    def shutdown(self):
        self.get_logger().info("Zamykanie wezla...")
        self.running = False
        try:
            self._send({'T': 131, 'cmd': 0})  # wylacz strumien feedbacku
        except Exception:
            pass
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()


def main(args=None):
    rclpy.init(args=args)
    node = UnifiedUgvNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()