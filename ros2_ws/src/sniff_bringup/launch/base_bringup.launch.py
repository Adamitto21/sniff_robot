import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    ugv_port = LaunchConfiguration('ugv_port')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_ugv_port = DeclareLaunchArgument(
        'ugv_port', default_value='/dev/ttyCH343USB0',
        description='Port szeregowy ESP32 (platforma UGV02)')
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Czas z symulacji zamiast systemowego')

    description_share = get_package_share_directory('robot_description')
    xacro_file = os.path.join(description_share, 'urdf', 'robot.urdf.xacro')

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(
                Command(['xacro ', xacro_file]), value_type=str),
            'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
        }],
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{'use_sim_time': ParameterValue(use_sim_time, value_type=bool)}],
    )

    odometry = Node(
        package='platform_control',
        executable='odometry',
        name='odometry',
        output='screen',
        parameters=[{
            'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
            'serial_port': ugv_port,
            'odom_frame': 'odom',
            'base_frame': 'base_footprint',
            'track_width': 0.40,
            'meters_per_tick': 0.00895,
            'min_angular_cmd': 0.30,
            'cmd_vel_timeout': 0.5,
        }],
    )

    return LaunchDescription([
        declare_ugv_port,
        declare_use_sim_time,
        robot_state_publisher,
        joint_state_publisher,
        odometry,
    ])