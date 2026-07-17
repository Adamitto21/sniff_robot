#!/usr/bin/env python3
"""
web_bringup.launch.py — backend panelu webowego sniff_robot

Uruchamia:
  - rosbridge_websocket  (port 9090) — most WebSocket <-> ROS2 dla przeglądarki
  - rosapi               — usługi typu /rosapi/topics (lista topików w panelu)
  - web_video_server     (port 8080) — strumień MJPEG z kamery dla <img>

Wymagane pakiety (w kontenerze):
  apt-get install -y ros-humble-rosbridge-suite ros-humble-web-video-server

Start:
  ros2 launch sniff_bringup web_bringup.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        # Most WebSocket dla przeglądarki
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_websocket',
            output='screen',
            parameters=[{
                'port': 9090,
                'address': '0.0.0.0',   # nasłuch na wszystkich interfejsach
            }],
        ),

        # Usługi rosapi (lista topików, typy, czas — używa ich panel)
        Node(
            package='rosapi',
            executable='rosapi_node',
            name='rosapi',
            output='screen',
        ),

        # Strumień MJPEG z topików obrazu
        Node(
            package='web_video_server',
            executable='web_video_server',
            name='web_video_server',
            output='screen',
            parameters=[{
                'port': 8080,
                'address': '0.0.0.0',
            }],
        ),
    ])
