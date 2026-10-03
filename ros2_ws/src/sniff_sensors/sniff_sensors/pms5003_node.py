#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sniff_msgs.msg import Pms5003
import serial
import struct


class Pms5003Node(Node):
    def __init__(self):
        super().__init__('pms5003_node')

        self.declare_parameter('sensor_port', '/dev/ttyUSB1')
        self.declare_parameter('publish_rate', 2.0)

        sensor_port = self.get_parameter('sensor_port').value
        rate = self.get_parameter('publish_rate').value

        self.pub = self.create_publisher(Pms5003, '/sniff/pms5003', 10)
        self.timer = self.create_timer(1.0 / rate, self.read_and_publish)

        try:
            self.ser = serial.Serial(sensor_port, baudrate=9600, timeout=3)
            self.ser.setDTR(False)
            self.ser.setRTS(False)
            self.get_logger().info(f'PMS5003 połączony na {sensor_port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Nie można otworzyć portu {sensor_port}: {e}')
            self.ser = None

    def read_and_publish(self):
        msg = Pms5003()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'pms5003'

        if self.ser is None:
            msg.sensor_ok = False
            self.pub.publish(msg)
            return

        try:
            self.ser.reset_input_buffer()

            # Synchronizacja na nagłówek
            byte1 = self.ser.read(1)
            if byte1 != b'\x42':
                msg.sensor_ok = False
                self.pub.publish(msg)
                return

            byte2 = self.ser.read(1)
            if byte2 != b'\x4d':
                msg.sensor_ok = False
                self.pub.publish(msg)
                return

            data = self.ser.read(28)
            if len(data) != 28:
                msg.sensor_ok = False
                self.pub.publish(msg)
                return

            values = struct.unpack('>HHHHHHHHHHHHHH', data)

            msg.pm1            = float(values[1])
            msg.pm25           = float(values[2])
            msg.pm10           = float(values[3])
            msg.particles_03um = values[5]
            msg.particles_05um = values[6]
            msg.particles_10um = values[7]
            msg.particles_25um = values[8]
            msg.sensor_ok      = True

            self.get_logger().info(
                f'PM1={msg.pm1} PM2.5={msg.pm25} PM10={msg.pm10} µg/m³'
            )

        except (serial.SerialException, struct.error) as e:
            self.get_logger().warn(f'Błąd odczytu PMS5003: {e}')
            msg.sensor_ok = False

        self.pub.publish(msg)

    def destroy_node(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Pms5003Node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
