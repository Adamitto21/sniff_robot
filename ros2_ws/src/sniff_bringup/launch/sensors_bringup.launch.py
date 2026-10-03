from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    sensor_port = LaunchConfiguration('sensor_port')

    declare_sensor_port = DeclareLaunchArgument(
        'sensor_port', default_value='/dev/ttyUSB1',
        description='Port szeregowy czujnika')

    pms5003 = Node(
        package='sniff_sensors',
        executable='pms5003_node',
        name='pms5003',
        output='screen',
        parameters=[{'sensor_port': sensor_port}],
    )

    return LaunchDescription([
        declare_sensor_port,
        pms5003,
    ])