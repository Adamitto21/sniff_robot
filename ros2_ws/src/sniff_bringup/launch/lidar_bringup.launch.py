import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    serial_port = LaunchConfiguration('serial_port')
    serial_baudrate = LaunchConfiguration('serial_baudrate')
    use_slam = LaunchConfiguration('use_slam')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_serial_port = DeclareLaunchArgument(
        'serial_port', default_value='/dev/ttyUSB1',
        description='Port szeregowy lidaru')
    declare_serial_baudrate = DeclareLaunchArgument(
        'serial_baudrate', default_value='115200',
        description='Baudrate lidaru (A1 = 115200)')
    declare_use_slam = DeclareLaunchArgument(
        'use_slam', default_value='true',
        description='Uruchamiac slam_toolbox razem z lidarem')
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Czas z symulacji zamiast systemowego')

    slam_toolbox_share = get_package_share_directory('slam_toolbox')
    description_share = get_package_share_directory('robot_description')
    slam_params = os.path.join(description_share, 'config', 'slam_params_hw.yaml')

    sllidar = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name='sllidar_node',
        output='screen',
        parameters=[{
            'serial_port': serial_port,
            # bez ParameterValue trafi tu tekst '115200', a sterownik chce int
            'serial_baudrate': ParameterValue(serial_baudrate, value_type=int),
            'frame_id': 'lidar_link',
            'inverted': False,
            'angle_compensate': True,
            'scan_mode': 'Standard',
        }],
    )

    # Opoznienie: slam_toolbox startuje po tym, jak lidar zdazy nadac pierwszy skan
    slam_toolbox = TimerAction(
        period=8.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(slam_toolbox_share, 'launch',
                                 'online_async_launch.py')),
                launch_arguments={
                    'use_sim_time': use_sim_time,
                    'slam_params_file': slam_params,
                }.items(),
                condition=IfCondition(use_slam),
            )
        ],
    )

    return LaunchDescription([
        declare_serial_port,
        declare_serial_baudrate,
        declare_use_slam,
        declare_use_sim_time,
        sllidar,
        slam_toolbox,
    ])