from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_recorder = LaunchConfiguration('use_recorder')

    declare_use_recorder = DeclareLaunchArgument(
        'use_recorder', default_value='true',
        description='Nagrywac rolling-buffer klipy z kamery')

    oak_detector = Node(
        package='sniff_vision',
        executable='oak_detector',
        name='oak_detector',
        output='screen',
    )

    video_recorder = Node(
        package='sniff_vision',
        executable='video_recorder',
        name='video_recorder',
        output='screen',
        condition=IfCondition(use_recorder),
    )

    return LaunchDescription([
        declare_use_recorder,
        oak_detector,
        video_recorder,
    ])
