#!/bin/bash
cd ~/r/sniff_robot
docker compose up -d
sleep 2
docker exec -d sniff_ros2 bash -c "source /opt/ros/humble/setup.bash && source /ros2_ws/install/setup.bash && ros2 run sniff_vision oak_detector"
docker exec -d sniff_ros2 bash -c "source /opt/ros/humble/setup.bash && source /ros2_ws/install/setup.bash && ros2 run sniff_vision web_viewer"
echo "Gotowe! Otwórz http://$(hostname -I | awk '{print $1}'):8080"
