import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import SetRemap


def generate_launch_description():
    robot_description_pkg = get_package_share_directory('robot_description')
    nav2_bringup = get_package_share_directory('nav2_bringup')

    nav2_params = os.path.join(robot_description_pkg, 'config', 'nav2_params.yaml')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # SetRemap dziala w ramach GroupAction - obejmuje caly dolaczony
    # navigation_launch.py wraz z jego wewnetrznymi node'ami. Bez tego
    # controller_server publikowalby na /cmd_vel, kolidujac z wyjsciem
    # twist_mux (patrz mux_bringup.launch.py).
    nav2_group = GroupAction([
        SetRemap(src='/cmd_vel', dst='/cmd_vel_nav'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup, 'launch', 'navigation_launch.py')),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'params_file': nav2_params,
                'autostart': 'true',
            }.items(),
        ),
    ])

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        nav2_group,
    ])
