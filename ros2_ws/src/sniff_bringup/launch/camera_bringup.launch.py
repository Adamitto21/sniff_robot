from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # 1. Detektor OAK
    oak_detector = Node(
        package='sniff_vision',
        executable='oak_detector',
        name='oak_detector',
        output='screen',
    )

    # 2. Podglad w przegladarce
    web_viewer = Node(
        package='sniff_vision',
        executable='web_viewer',
        name='web_viewer',
        output='screen',
    )

    return LaunchDescription([
        oak_detector,
        web_viewer,
    ])