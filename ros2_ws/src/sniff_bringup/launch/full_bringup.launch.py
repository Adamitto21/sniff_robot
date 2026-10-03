import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    serial_port = LaunchConfiguration('serial_port')
    sensor_port = LaunchConfiguration('sensor_port')
    serial_baudrate = LaunchConfiguration('serial_baudrate')
    ugv_port = LaunchConfiguration('ugv_port')

    declare_serial_port = DeclareLaunchArgument(
        'serial_port', default_value='/dev/ttyUSB0',
        description='Port szeregowy lidaru')
    declare_sensor_port = DeclareLaunchArgument(
        'sensor_port', default_value='/dev/ttyUSB1',
        description='Port szeregowy czujnika')
    declare_serial_baudrate = DeclareLaunchArgument(
        'serial_baudrate', default_value='115200',
        description='Baudrate lidaru (A1 = 115200)')
    declare_ugv_port = DeclareLaunchArgument(
        'ugv_port', default_value='/dev/ttyCH343USB0',
        description='Port szeregowy ESP32 (platforma UGV02)')

    declare_use_autonomy = DeclareLaunchArgument('use_autonomy', default_value='true')
    declare_use_camera = DeclareLaunchArgument('use_camera', default_value='true')
    declare_use_sensors = DeclareLaunchArgument('use_sensors', default_value='true')
    declare_use_web = DeclareLaunchArgument('use_web', default_value='true')

    launch_dir = os.path.join(
        get_package_share_directory('sniff_bringup'), 'launch')

    def include(name, condition_arg, args=None):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(launch_dir, name)),
            launch_arguments=(args or {}).items(),
            condition=IfCondition(LaunchConfiguration(condition_arg)),
        )

    autonomy = include('autonomy_bringup.launch.py', 'use_autonomy',
                   {'ugv_port': ugv_port,
                    'serial_port': serial_port,
                    'serial_baudrate': serial_baudrate})
    camera = include('camera_bringup.launch.py', 'use_camera')
    sensors = include('sensors_bringup.launch.py', 'use_sensors',
                    {'sensor_port': sensor_port})
    web = include('web_bringup.launch.py', 'use_web')

    return LaunchDescription([
        declare_serial_port,
        declare_sensor_port,
        declare_serial_baudrate,
        declare_ugv_port,
        declare_use_autonomy,
        declare_use_camera,
        declare_use_sensors,
        declare_use_web,
        autonomy,
        camera,
        sensors,
        web,
    ])