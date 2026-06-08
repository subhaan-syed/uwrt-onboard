FROM osrf/ros:humble-desktop

# Install turtlesim, CycloneDDS, and colcon (the ROS2 build tool)
# CycloneDDS replaces the default Fast-DDS middleware, which hangs on Mac Docker
# due to UDP multicast not working on Docker's virtual network on macOS
RUN apt-get update && apt-get install -y \
    ros-humble-turtlesim \
    ros-humble-rmw-cyclonedds-cpp \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# Use CycloneDDS as the ROS middleware
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

WORKDIR /ros2_ws

# Copy our custom ROS2 package source into the workspace
COPY src/ src/

# Build the workspace with colcon.
# We source the base ROS2 install first so colcon knows about ROS2 dependencies.
RUN bash -c "source /opt/ros/humble/setup.bash && colcon build --symlink-install"

# Source both ROS2 and our built workspace in every shell session.
# The workspace source must come after the ROS2 source.
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc
