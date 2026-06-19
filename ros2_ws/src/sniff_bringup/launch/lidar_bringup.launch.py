import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # --- Argumenty (mozna nadpisac z linii polecen) ---
    serial_port = LaunchConfiguration('serial_port')
    serial_baudrate = LaunchConfiguration('serial_baudrate')

    declare_serial_port = DeclareLaunchArgument(
        'serial_port', default_value='/dev/ttyUSB0',
        description='Port szeregowy lidaru')
    declare_serial_baudrate = DeclareLaunchArgument(
        'serial_baudrate', default_value='115200',
        description='Baudrate lidaru (A1 = 115200)')

    # --- Sciezki do pakietow ---
    sllidar_share = get_package_share_directory('sllidar_ros2')
    slam_toolbox_share = get_package_share_directory('slam_toolbox')

    # 1. Lidar SLLIDAR A1
    sllidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sllidar_share, 'launch', 'sllidar_a1_launch.py')),
        launch_arguments={
            'serial_port': serial_port,
            'serial_baudrate': serial_baudrate,
        }.items()
    )

    # 2. TF: odom -> base_link
    tf_odom_base = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_odom_base_link',
        arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link'],
        output='screen',
    )

    # 3. TF: base_link -> laser
    tf_base_laser = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_base_link_laser',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'laser'],
        output='screen',
    )

    # 4. slam_toolbox (online async)
    # Opozniony o kilka sekund, zeby zdazyl pojawic sie skan i TF.
    slam_toolbox = TimerAction(
        period=5.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(slam_toolbox_share, 'launch',
                                 'online_async_launch.py')),
            )
        ]
    )

    return LaunchDescription([
        declare_serial_port,
        declare_serial_baudrate,
        sllidar,
        tf_odom_base,
        tf_base_laser,
        slam_toolbox,
    ])