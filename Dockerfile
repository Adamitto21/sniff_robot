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
    ros-humble-teleop-twist-keyboard \
    python3-serial \
    && rm -rf /var/lib/apt/lists/*

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc
RUN echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

WORKDIR /ros2_ws