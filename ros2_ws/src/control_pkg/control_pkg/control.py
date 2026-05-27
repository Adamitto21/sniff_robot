import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class ControlNode(Node):
    def __init__(self):
        super().__init__('control_node')
        self.get_logger().info('Utworzono node "ControlNode"')
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)

    def move(self, cmd_str):
        msg = Twist()

        if cmd_str == 'w':
            msg.linear.x = 0.5
        elif cmd_str == 's':
            msg.linear.x = -0.5
        elif cmd_str == 'a':
            msg.angular.z = 0.2
        elif cmd_str == 'd':
            msg.angular.z = -0.2
        elif cmd_str == 'x':
            msg.linear.z = 0.0
            msg.angular.z = 0.0
        else:
            self.get_logger().warning('Nieznana komenda!')
            return
        
        self.publisher.publish(msg)
        self.get_logger().info(f'Wyslano komende: {cmd_str}')


def main(args=None):
    rclpy.init(args=args)
    node = ControlNode()

    try:
        while rclpy.ok():
            print('Wpisz komende byku')
            try:
                user_input = input().strip().lower()
                node.move(user_input)
            except EOFError:
                break
    except KeyboardInterrupt:
        node.get_logger().info('Zakonczono Ctrl+C')
    finally:
        node.move('x')
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
