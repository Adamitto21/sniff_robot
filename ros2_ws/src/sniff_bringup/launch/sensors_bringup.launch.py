from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pms5003 = Node(
        package='sniff_sensors',
        executable='pms5003_node',
        name='pms5003',
        output='screen',
    )

    return LaunchDescription([
        pms5003,
    ])