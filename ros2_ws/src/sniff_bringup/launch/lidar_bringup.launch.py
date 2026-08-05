import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # --- Argumenty ---
    serial_port = LaunchConfiguration('serial_port')
    serial_baudrate = LaunchConfiguration('serial_baudrate')
    ugv_port = LaunchConfiguration('ugv_port')

    declare_serial_port = DeclareLaunchArgument(
        'serial_port', default_value='/dev/ttyUSB0',
        description='Port szeregowy lidaru')
    declare_serial_baudrate = DeclareLaunchArgument(
        'serial_baudrate', default_value='115200',
        description='Baudrate lidaru (A1 = 115200)')
    declare_ugv_port = DeclareLaunchArgument(
        'ugv_port', default_value='/dev/ttyCH343USB0',
        description='Port szeregowy ESP32 (platforma UGV02)')

    # --- Sciezki do pakietow ---
    sllidar_share = get_package_share_directory('sllidar_ros2')
    slam_toolbox_share = get_package_share_directory('slam_toolbox')
    robot_description_share = get_package_share_directory('robot_description')

    xacro_file = os.path.join(robot_description_share, 'urdf', 'robot.urdf.xacro')
    slam_params = os.path.join(robot_description_share, 'config', 'slam_params_hw.yaml')

    # 1. Model robota z URDF
    #    ZMIANA: zastepuje statyczne TF base_link->laser.
    #    Nav2 i costmapa potrzebuja pelnej geometrii robota.
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(
                Command(['xacro ', xacro_file]), value_type=str),
            'use_sim_time': False,
        }]
    )

    # 2. Sterowanie platforma + odometria z enkoderow
    #    ZMIANA: zastepuje statyczne TF odom->base_link (transformata
    #    tozsamosciowa oznaczala, ze robot nigdy sie nie porusza - Nav2 na tym
    #    nie ruszy). Teraz odom->base_footprint z rzeczywistej odometrii.
    unified_ugv = Node(
        package='platform_control',
        executable='odometry',
        name='unified_ugv_node',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'serial_port': ugv_port,
            'odom_frame': 'odom',
            'base_frame': 'base_footprint',
            'track_width': 0.44,
            'meters_per_tick': 0.0105,
            'min_angular_cmd': 0.08,
            'cmd_vel_timeout': 0.5,
        }]
    )

    # 3. Lidar SLLIDAR A1
    #    ZMIANA: frame_id ustawiony na lidar_link (zgodnie z URDF).
    #    Domyslnie driver publikuje 'laser', czego SLAM nie znajdzie w TF.
    sllidar = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name='sllidar_node',
        output='screen',
        parameters=[{
            'serial_port': serial_port,
            'serial_baudrate': serial_baudrate,
            'frame_id': 'lidar_link',
            'inverted': False,
            'angle_compensate': True,
            'scan_mode': 'Standard',
        }]
    )

    # 4. slam_toolbox (online async)
    #    ZMIANA: wlasny plik parametrow (use_sim_time: false) zamiast
    #    sciezki na sztywno. Opoznienie zwiekszone do 8 s.
    slam_toolbox = TimerAction(
        period=8.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(slam_toolbox_share, 'launch',
                                 'online_async_launch.py')),
                launch_arguments={
                    'use_sim_time': 'false',
                    'slam_params_file': slam_params,
                }.items()
            )
        ]
    )

    return LaunchDescription([
        declare_serial_port,
        declare_serial_baudrate,
        declare_ugv_port,
        robot_state_publisher,
        unified_ugv,
        sllidar,
        slam_toolbox,
    ])