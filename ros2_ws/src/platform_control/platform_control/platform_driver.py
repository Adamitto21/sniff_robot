import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import json

class PlatformDriver(Node):
    def __init__(self):
        super().__init__('platform_driver')
        self.get_logger().info('Node platform_driver uruchomiony')
        self.serial_port = '/dev/ttyCH343USB0'
        self.baud_rate = 115200

        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            self.get_logger().info(f'Polaczono z ugv02 na porice {self.serial_port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Blad polaczenia z portem: {e}')
            self.ser = None
    
        self.subscription = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)

    def cmd_vel_callback(self, msg):
        if self.ser is None or not self.ser.is_open:
            return
        
        linear = msg.linear.x
        angular = msg.angular.z

        l_speed = linear - angular
        r_speed = linear + angular

        l_speed = max(min(l_speed, 1.0), -1.0)
        r_speed = max(min(r_speed, 1.0), -1.0)

        if l_speed == 0 and r_speed == 0:
            command = {'T':0}
        else:
            command = {'T':1, 'L':round(l_speed, 3), 'R':round(r_speed, 3)}

        try:
            json_str = json.dumps(command) + '\n'
            self.ser.write(json_str.encode('utf-8'))
        except Exception as e:
            self.get_logger().error(f'Blad wyslania, blad: {e}')
        
    def stop_platform(self):
        if self.ser and self.ser.is_open:
            self.get_logger().info('Zatrzymywanie')
            try:
                self.ser.write((json.dumps({'T':0}) + '\n').encode('utf-8'))
                self.ser.close()
            except Exception as e:
                self.get_logger().error(f'Blad: {e}')
    
def main(args=None):
    rclpy.init(args=args)
    node = PlatformDriver()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info(f'Przerwano z klawiatury')
    finally:
        node.stop_platform()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()