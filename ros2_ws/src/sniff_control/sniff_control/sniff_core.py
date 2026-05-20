import rclpy
from rclpy.node import Node

class SniffCoreNode(Node):
    def __init__(self):
        # Nazwa węzła widoczna w systemie ROS
        super().__init__('sniff_core_node')
        self.get_logger().info('System SNIFF uruchomiony. Oczekuję na podłączenie platformy UGV02...')

def main(args=None):
    rclpy.init(args=args)
    node = SniffCoreNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()