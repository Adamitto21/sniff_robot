#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import serial
import json
import math
import threading
import os
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from std_msgs.msg import Float32

def euler_to_quaternion(roll, pitch, yaw):
    qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
    qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
    qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    return [qx, qy, qz, qw]

class UnifiedUgvNode(Node):
    def __init__(self):
        super().__init__('unified_ugv_node')
        
        self.wheel_base = 0.20  # Odległość między kołami (L) w metrach
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        self.last_time = self.get_clock().now()

        serial_port = '/dev/ttyCH343USB0'
        try:
            self.ser = serial.Serial(serial_port, 115200, timeout=1)
            self.get_logger().info(f"Połączono z mikrokontrolerem na porcie: {serial_port}")
        except Exception as e:
            self.get_logger().error(f"Błąd otwarcia portu szeregowego: {e}")
            raise e

        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.voltage_pub = self.create_publisher(Float32, 'voltage', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)

        # 6. URUCHOMIENIE WĄTKU ODBIORU (UART Read Loop)
        self.running = True
        self.read_thread = threading.Thread(target=self.uart_receive_loop, daemon=True)
        self.read_thread.start()

    def cmd_vel_callback(self, msg):
        """Callback odbierający prędkość z ROS i wysyłający ją do ESP32."""
        linear_velocity = msg.linear.x
        angular_velocity = msg.angular.z

        # Filtr progowy dla małych prędkości obrotowych (z oryginalnego kodu Waveshare)
        if linear_velocity == 0:
            if 0 < angular_velocity < 0.2:
                angular_velocity = 0.2
            elif -0.2 < angular_velocity < 0:
                angular_velocity = -0.2

        command_data = json.dumps({'T': '13', 'X': linear_velocity, 'Z': angular_velocity}) + "\n"
        try:
            self.ser.write(command_data.encode('utf-8'))
        except Exception as e:
            self.get_logger().warn(f"Nie udało się wysłać cmd_vel przez UART: {e}")

    def uart_receive_loop(self):
        """Pętla w tle czytająca dane telemetryczne z enkoderów."""
        while self.running and rclpy.ok():
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    data = json.loads(line)
                    # Sprawdzenie typu wiadomości (1001 = telemetria sprzętowa)
                    if data.get("T") == 1001:
                        self.update_and_publish_odometry(data)
                        self.publish_voltage(data)
            except json.JSONDecodeError:
                pass  # Ignoruj niepełne ramki szeregowe
            except Exception as e:
                if self.running:
                    self.get_logger().warn(f"Błąd w pętli UART: {e}")

    def update_and_publish_odometry(self, data):
        """Wylicza kinematykę i publikuje dane odometrii oraz TF."""
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        
        if dt <= 0:
            return

        # Pobieranie prędkości kół (zakładamy, że odl/odr to prędkość przetworzona na cm/s)
        v_left = float(data.get("odl", 0)) / 100.0
        v_right = float(data.get("odr", 0)) / 100.0

        # Model kinematyczny robota o napędzie różnicowym
        v = (v_right + v_left) / 2.0
        w = (v_right - v_left) / self.wheel_base

        # Integracja po czasie (obliczanie nowej pozycji)
        delta_x = (v * math.cos(self.th)) * dt
        delta_y = (v * math.sin(self.th)) * dt
        delta_th = w * dt

        self.x += delta_x
        self.y += delta_y
        self.th += delta_th

        # Konwersja kąta orientacji na kwaternion
        q = euler_to_quaternion(0, 0, self.th)

        # 1. Publikacja transformacji układów współrzędnych (TF: odom -> base_link)
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
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

        # 2. Publikacja wiadomości Odometry na topiku /odom
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
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
        self.odom_pub.publish(odom)

        self.last_time = current_time

    def publish_voltage(self, data):
        """Publikuje napięcie baterii."""
        if "v" in data:
            msg = Float32()
            msg.data = float(data["v"]) / 100.0
            self.voltage_pub.publish(msg)

    def shutdown(self):
        """Bezpieczne zatrzymanie wątków i zamknięcie portu."""
        self.get_logger().info("Zamykanie zintegrowanego węzła...")
        self.running = False
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