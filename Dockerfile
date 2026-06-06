FROM osrf/ros:humble-desktop

# Install turtlesim and CycloneDDS
# CycloneDDS replaces the default Fast-DDS middleware, which hangs on Mac Docker
# due to UDP multicast not working on Docker's virtual network on macOS
RUN apt-get update && apt-get install -y \
    ros-humble-turtlesim \
    ros-humble-rmw-cyclonedds-cpp \
    && rm -rf /var/lib/apt/lists/*

# Use CycloneDDS as the ROS middleware
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Source ROS2 automatically in every shell session
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

WORKDIR /ros2_ws
