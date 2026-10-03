"""twist_mux — arbitraz miedzy nav2 a sterowaniem recznym z panelu.

Bez tego oba zrodla publikuja na /cmd_vel jednoczesnie i robot dostaje
sprzeczne komendy. Przelacznik w panelu dziala dopiero wtedy, gdy ten
node jest uruchomiony.

WYMAGA jednej zmiany po stronie nav2: controller_server musi publikowac
na /cmd_vel_nav zamiast /cmd_vel. W nav2.launch.py (platform_control) dodaj
do node'a controller_server:

    remappings=[('/cmd_vel', '/cmd_vel_nav')]

Sprawdzenie po uruchomieniu:
    ros2 topic info /cmd_vel        -> publisher: twist_mux (jeden!)
    ros2 topic echo /cmd_vel_nav    -> komendy nav2
    ros2 topic echo /manual_lock    -> blokada z panelu
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    config = LaunchConfiguration('config')

    declare_config = DeclareLaunchArgument(
        'config',
        default_value=os.path.join(
            get_package_share_directory('sniff_bringup'), 'config', 'twist_mux.yaml'),
        description='Plik z priorytetami zrodel sterowania')

    twist_mux = Node(
        package='twist_mux',
        executable='twist_mux',
        name='twist_mux',
        output='screen',
        parameters=[config],
        # twist_mux domyslnie publikuje na cmd_vel_out — kierujemy to na cmd_vel,
        # czyli tam, gdzie sluchа sterownik platformy
        remappings=[('/cmd_vel_out', '/cmd_vel')],
    )

    return LaunchDescription([declare_config, twist_mux])