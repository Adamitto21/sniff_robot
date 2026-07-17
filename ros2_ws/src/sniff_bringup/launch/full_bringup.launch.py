import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    bringup_share = get_package_share_directory('sniff_bringup')
    launch_dir = os.path.join(bringup_share, 'launch')

    # Lidar + TF + slam_toolbox
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'lidar_bringup.launch.py'))
    )

    # Kamera OAK + web viewer
    camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'camera_bringup.launch.py'))
    )

    return LaunchDescription([
        lidar,
        camera,
    ])