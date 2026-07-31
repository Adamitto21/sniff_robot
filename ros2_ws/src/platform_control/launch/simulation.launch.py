import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    robot_description_pkg = get_package_share_directory('robot_description')
    
    xacro_file = os.path.join(robot_description_pkg, 'urdf', 'robot.urdf.xacro')
    world_file = os.path.join(robot_description_pkg, 'worlds', 'sniff_indoor.world')
    gazebo_pkg = get_package_share_directory('gazebo_ros')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gazebo_pkg, 'launch', 'gazebo.launch.py')),
        launch_arguments={'world': world_file}.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(Command(['xacro ', xacro_file]), value_type=str),
            'use_sim_time': True
    }]
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'my_six_wheeler', '-x', '-4.0', '-y', '0.0', '-z', '0.10',
                           '-Y', '0.0'],
        output='screen',
    )

    slam_toolbox_pkg = get_package_share_directory('slam_toolbox')
    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(slam_toolbox_pkg, 'launch', 'online_async_launch.py')),
        launch_arguments={'use_sim_time': 'true'}.items()
    )

    # 5. RVIZ2
    rviz_config_file = os.path.join(robot_description_pkg, 'rviz_conf', 'config_rviz2.rviz')

    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_entity,
        TimerAction(
            period=3.0,
            actions=[slam_toolbox, rviz2]
        )
    ])