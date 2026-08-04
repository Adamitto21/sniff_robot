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

    #paczki do symulacji
    ros-humble-xacro \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-urdf-tutorial \
    ros-humble-teleop-twist-keyboard \
    ros-humble-gazebo-ros-pkgs \

    #paczki do strony internetowej
    ros-humble-rosbridge-suite \
    ros-humble-web-video-server \
    
    
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install depthai==2.24.0.0

RUN mkdir -p /root/.gazebo/models && \
    git clone https://github.com/osrf/gazebo_models.git /root/.gazebo/models

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc
RUN echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

WORKDIR /ros2_ws