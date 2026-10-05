FROM ros:humble-perception

RUN apt-get update && apt-get install -y \
    #niezbedne paczki
    python3-colcon-common-extensions \
    python3-pip \
    python3-serial \
    nano \
    iputils-ping \
    net-tools \
    usbutils \
    #dodatkowe paczki rosa
    ros-humble-rviz2 \
    ros-humble-rqt \
    ros-humble-rqt-common-plugins \
    #paczki do lidara
    ros-humble-rplidar-ros \
    ros-humble-slam-toolbox \
    #paczki do kamery
    ros-humble-vision-msgs \
    ros-humble-cv-bridge \
    #paczki do autonomicznego poruszania sie
    ros-humble-nav2-costmap-2d \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-pointcloud-to-laserscan \
    ros-humble-diagnostic-updater \
    ros-humble-nav2-msgs \
    ros-humble-map-msgs \
    #paczki do modelu robota
    ros-humble-xacro \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-urdf-tutorial \
    ros-humble-teleop-twist-keyboard \
    #paczki do strony internetowej
    ros-humble-rosbridge-suite \
    ros-humble-web-video-server \
    ros-humble-twist-mux \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install depthai==2.24.0.0

# Frontier exploration - osobny workspace poza mountem /ros2_ws
RUN mkdir -p /deps_ws/src && \
    git clone --depth 1 https://github.com/robo-friends/m-explore-ros2.git /deps_ws/src/m-explore-ros2 && \
    cd /deps_ws && \
    . /opt/ros/humble/setup.sh && \
    colcon build --packages-up-to explore_lite && \
    cp /deps_ws/src/m-explore-ros2/LICENSE /deps_ws/install/explore_lite/share/explore_lite/LICENSE 2>/dev/null || \
    cp /deps_ws/src/m-explore-ros2/LICENSE /deps_ws/install/LICENSE && \
    rm -rf /deps_ws/build /deps_ws/log /deps_ws/src

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc
RUN echo "[ -f /deps_ws/install/setup.bash ] && source /deps_ws/install/setup.bash" >> /root/.bashrc
RUN echo "[ -f /ros2_ws/install/setup.bash ] && source /ros2_ws/install/setup.bash" >> /root/.bashrc

WORKDIR /ros2_ws
