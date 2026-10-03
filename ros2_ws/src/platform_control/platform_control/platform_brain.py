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
        self.declare_parameter('serial_port', '/dev/ttyCH343USB0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('track_width', 0.172)
        self.declare_parameter('meters_per_tick', 0.00895)
        self.declare_parameter('max_tick_delta', 100)

        self.declare_parameter('min_angular_cmd', 0.30)

        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_footprint')

        self.declare_parameter('cmd_vel_timeout', 0.5)


        self.declare_parameter('motor_pid_p', 0)
        self.declare_parameter('motor_pid_i', 800)
        self.declare_parameter('motor_pid_d', 0)

        self.serial_port = self.get_parameter('serial_port').value
        baudrate = self.get_parameter('baudrate').value
        self.track_width = self.get_parameter('track_width').value
        self.mpt = self.get_parameter('meters_per_tick').value
        self.max_tick_delta = self.get_parameter('max_tick_delta').value
        self.min_angular_cmd = self.get_parameter('min_angular_cmd').value
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.cmd_vel_timeout = self.get_parameter('cmd_vel_timeout').value
        self.motor_pid_p = self.get_parameter('motor_pid_p').value
        self.motor_pid_i = self.get_parameter('motor_pid_i').value
        self.motor_pid_d = self.get_parameter('motor_pid_d').value

        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        self.odl_prev = None
        self.odr_prev = None

        self.last_odom_time = None

        try:
            self.ser = serial.Serial(self.serial_port, baudrate, timeout=1)
            time.sleep(2.0)
            self.ser.reset_input_buffer()
            self.get_logger().info(f"Polaczono z ESP32 na porcie: {self.serial_port}")
        except Exception as e:
            self.get_logger().error(f"Blad otwarcia portu szeregowego: {e}")
            raise e

        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)

        self.enable_feedback_stream()
        self.create_timer(5.0, self.enable_feedback_stream)

        self.set_motor_pid()


        self.last_cmd_time = self.get_clock().now()
        self.stopped = True
        self.create_timer(0.2, self.cmd_watchdog)

        self.running = True
        self.read_thread = threading.Thread(target=self.uart_receive_loop, daemon=True)
        self.read_thread.start()

    def _send(self, obj):
        try:
            self.ser.write((json.dumps(obj) + "\n").encode('utf-8'))
        except Exception as e:
            self.get_logger().warn(f"Nie udalo sie wyslac przez UART: {e}")

    def enable_feedback_stream(self):
        self._send({'T': 131, 'cmd': 1})

    def set_motor_pid(self):
        self._send({
            'T': 2,
            'P': self.motor_pid_p,
            'I': self.motor_pid_i,
            'D': self.motor_pid_d,
            'L': 255,
        })
        self.get_logger().info(
            f"Ustawiono PID silnikow: P={self.motor_pid_p}, "
            f"I={self.motor_pid_i}, D={self.motor_pid_d}")

    def cmd_watchdog(self):
        dt = (self.get_clock().now() - self.last_cmd_time).nanoseconds / 1e9
        if dt > self.cmd_vel_timeout and not self.stopped:
            self._send({'T': 13, 'X': 0.0, 'Z': 0.0})
            self.stopped = True
            self.get_logger().warn(
                f"Brak /cmd_vel przez {dt:.1f}s - STOP")

    def cmd_vel_callback(self, msg):
        self.last_cmd_time = self.get_clock().now()
        self.stopped = False

        linear_velocity = msg.linear.x
        angular_velocity = msg.angular.z

        if abs(linear_velocity) < 1e-6 and 1e-6 < abs(angular_velocity) < self.min_angular_cmd:
            angular_velocity = math.copysign(self.min_angular_cmd, angular_velocity)

        self._send({'T': 13, 'X': float(linear_velocity), 'Z': float(angular_velocity)})

    def uart_receive_loop(self):
        while self.running and rclpy.ok():
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    data = json.loads(line)
                    if data.get("T") == 1001:
                        self.update_and_publish_odometry(data)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                if self.running:
                    self.get_logger().warn(f"Blad w petli UART: {e}")

    def update_and_publish_odometry(self, data):
        try:
            odl = int(data["odl"])
            odr = int(data["odr"])
        except (KeyError, ValueError, TypeError):
            return

        current_time = self.get_clock().now()

        if self.odl_prev is None:
            self.odl_prev = odl
            self.odr_prev = odr
            return

        delta_l_ticks = odl - self.odl_prev
        delta_r_ticks = odr - self.odr_prev

        if abs(delta_l_ticks) > self.max_tick_delta or abs(delta_r_ticks) > self.max_tick_delta:
            self.odl_prev = odl
            self.odr_prev = odr
            return

        self.odl_prev = odl
        self.odr_prev = odr

        d_left = delta_l_ticks * self.mpt
        d_right = delta_r_ticks * self.mpt

        d_center = (d_left + d_right) / 2.0
        d_theta = (d_right - d_left) / self.track_width

        self.x += d_center * math.cos(self.th + d_theta / 2.0)
        self.y += d_center * math.sin(self.th + d_theta / 2.0)
        self.th += d_theta
        self.th = math.atan2(math.sin(self.th), math.cos(self.th))

        if self.last_odom_time is not None:
            dt = (current_time - self.last_odom_time).nanoseconds / 1e9
        else:
            dt = 0.0
        self.last_odom_time = current_time

        if dt > 0.001:
            v = d_center / dt
            w = d_theta / dt
        else:
            v = 0.0
            w = 0.0

        q = euler_to_quaternion(0, 0, self.th)
        stamp = current_time.to_msg()

        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = self.odom_frame
        t.child_frame_id = self.base_frame
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]
        self.tf_broadcaster.sendTransform(t)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.x = q[0]
        odom.pose.pose.orientation.y = q[1]
        odom.pose.pose.orientation.z = q[2]
        odom.pose.pose.orientation.w = q[3]
        odom.twist.twist.linear.x = v
        odom.twist.twist.angular.z = w

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
            self._send({'T': 13, 'X': 0.0, 'Z': 0.0})
            time.sleep(0.1)
            self._send({'T': 131, 'cmd': 0})
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
