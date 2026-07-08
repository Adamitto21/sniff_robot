from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package = 'ugv_tools',
            executable = 'keyboard_ctrl',
            output = 'screen'
        ),
        Node(
            package = 'rqt_graph',
            executable = 'rqt_graph',
            output = 'screen'
        ),
        Node(
            package = 'platform_control',
            executable = 'odometry',
            output = 'screen'
        )
    ])