import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    robot_description_pkg = get_package_share_directory('robot_description')
    params_file = os.path.join(robot_description_pkg, 'config', 'explore_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),

        Node(
            package='explore_lite',
            name='explore_node',
            executable='explore',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
            output='screen',
        ),
    ])