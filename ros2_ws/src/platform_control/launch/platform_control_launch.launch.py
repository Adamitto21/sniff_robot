from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package = 'platform_control',
            executable = 'platform_driver',
            output = 'screen'
        ),
        Node(
            package = 'platform_control',
            executable = 'keyboard',
            output = 'screen'
        ),
        Node(
            package = 'rqt_graph',
            executable = 'rqt_graph',
            output = 'screen'
        )
        Node(
            package = 'platform_control',
            executable = 'platform_brain',
            output = 'screen'
        )
    ])