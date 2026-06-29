FROM ros:humble-perception

RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-pip \
    nano \
    iputils-ping \
    net-tools \
    usbutils \
    ros-humble-rviz2 \
    ros-humble-rqt \
    ros-humble-rqt-common-plugins \
    ros-humble-rplidar-ros \
    ros-humble-slam-toolbox \
    ros-humble-vision-msgs \
    ros-humble-cv-bridge \
    python3-serial \
    ros-humble-nav2-costmap-2d \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-xacro \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-rosbridge-suite \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install depthai==2.24.0.0

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc
RUN echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

WORKDIR /ros2_ws