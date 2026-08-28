import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            LogInfo, TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    serial_port = LaunchConfiguration('serial_port')
    serial_baudrate = LaunchConfiguration('serial_baudrate')
    ugv_port = LaunchConfiguration('ugv_port')

    declares = [
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB1',
                              description='Port szeregowy lidaru'),
        DeclareLaunchArgument('serial_baudrate', default_value='115200',
                              description='Baudrate lidaru (A1 = 115200)'),
        DeclareLaunchArgument('ugv_port', default_value='/dev/ttyCH343USB0',
                              description='Port szeregowy ESP32 (UGV02)'),

        # Flagi: ustaw na false to, co juz dziala z innego launcha
        DeclareLaunchArgument('use_base', default_value='true',
                              description='Odometria, TF i opis robota'),
        DeclareLaunchArgument('use_lidar', default_value='true',
                              description='Lidar i slam_toolbox'),
        DeclareLaunchArgument('use_nav2', default_value='true'),
        DeclareLaunchArgument('use_explore', default_value='true'),
        
        # Opoznienia — zwieksz, jesli Jetson startuje wolniej
        DeclareLaunchArgument('nav2_delay', default_value='20.0',
                              description='Sekundy przed startem nav2'),
        DeclareLaunchArgument('explore_delay', default_value='32.0',
                              description='Sekundy przed startem explore'),
    ]

    sniff_launch = os.path.join(
        get_package_share_directory('sniff_bringup'), 'launch')
    platform_launch = os.path.join(
        get_package_share_directory('platform_control'), 'launch')

    def include(path, flag, args=None):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(path),
            launch_arguments=(args or {}).items(),
            condition=IfCondition(LaunchConfiguration(flag)),
        )

    # --- 0 s: podstawa robota ---
    base = include(os.path.join(sniff_launch, 'base_bringup.launch.py'),
                   'use_base', {'ugv_port': ugv_port})

    mux = include(os.path.join(sniff_launch, 'mux_bringup.launch.py'), 'use_base')

    # --- 0 s: lidar (slam startuje w srodku po 8 s) ---
    lidar = include(os.path.join(sniff_launch, 'lidar_bringup.launch.py'),
                    'use_lidar', {'serial_port': serial_port,
                                  'serial_baudrate': serial_baudrate,
                                  'use_slam': 'true'})

    # --- nav2: dopiero gdy jest mapa i TF map->odom ---
    nav2 = TimerAction(
        period=LaunchConfiguration('nav2_delay'),
        actions=[
            LogInfo(msg='[autonomy] startuje nav2...'),
            include(os.path.join(platform_launch, 'nav2.launch.py'), 'use_nav2'),
        ],
    )

    # --- explore: dopiero gdy serwery nav2 przyjmuja cele ---
    explore = TimerAction(
        period=LaunchConfiguration('explore_delay'),
        actions=[
            LogInfo(msg='[autonomy] startuje eksploracje...'),
            include(os.path.join(platform_launch, 'explore.launch.py'),
                    'use_explore'),
        ],
    )

    return LaunchDescription(declares + [
        LogInfo(msg='[autonomy] start: base + lidar, potem nav2, na koncu explore'),
        base,
        mux,
        lidar,
        nav2,
        explore,
    ])