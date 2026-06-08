# ROS2 Turtlesim Project

This project demonstrates how to use the `turtlesim` package in ROS2 Humble to control a turtle using both keyboard input and command-line topic publishing. It also includes a custom ROS2 node (`turtle_magic`) that drives the turtle in a square when triggered by a service call. Everything runs inside a Docker container on macOS (Apple Silicon) with GUI forwarding through XQuartz.

---

## Project Objectives

- Launch the turtlesim node and get the turtle window showing on screen
- Control the turtle with keyboard input
- List active ROS2 topics
- Change the background color using parameters
- Move the turtle in a continuous circle using command-line topic publishing
- Write a custom ROS2 publisher/service node that draws a square path on demand

---

## Environment

- macOS (Apple Silicon M2)
- Docker Desktop with ROS2 Humble (osrf/ros:humble-desktop)
- XQuartz for X11 GUI forwarding
- CycloneDDS middleware (replaces default Fast-DDS to fix Mac Docker networking)

---

## Setup

### 1. Build the Docker image

```bash
docker build -t ros2-humble-turtlesim .
```

### 2. Allow XQuartz to accept connections

```bash
open -a XQuartz
xhost + 127.0.0.1
```

### 3. Start the container

```bash
docker run -d \
  --name ros2_turtlesim \
  -e DISPLAY=host.docker.internal:0 \
  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
  ros2-humble-turtlesim \
  bash -c "source /opt/ros/humble/setup.bash && ros2 run turtlesim turtlesim_node"
```

The turtlesim window will appear on your screen via XQuartz.

---

## Steps and Results

### 1. Launch turtlesim

```bash
ros2 run turtlesim turtlesim_node
```

This opens the turtle simulation window with a turtle in the center.

### 2. Move the turtle with keyboard

In a separate terminal, run:

```bash
docker exec -it ros2_turtlesim bash -c "source /opt/ros/humble/setup.bash && ros2 run turtlesim turtle_teleop_key"
```

Use the arrow keys to control the turtle:
- Up / Down arrows: move forward and backward
- Left / Right arrows: rotate in place

### 3. List active topics

```bash
ros2 topic list
```

Output:
```
/parameter_events
/rosout
/turtle1/cmd_vel
/turtle1/color_sensor
/turtle1/pose
```

### 4. Change background color

```bash
ros2 param set /turtlesim background_b 200
ros2 service call /clear std_srvs/srv/Empty
```

This sets the blue channel of the background to 200 and refreshes the window.

### 5. Move the turtle in a circle using the command line

```bash
ros2 topic pub /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0}, angular: {z: 1.0}}"
```

This publishes a velocity command directly to the turtle, sending it in a continuous circle without any keyboard input.

---

## The Magic Button

The `turtle_magic` package contains a custom ROS2 node called `path_drawer`. It advertises a service called `/draw_path`. Calling that service is the "magic button" -- the turtle immediately drives itself in a square and stops when it is done.

Internally, the node uses:
- A **publisher** on `/turtle1/cmd_vel` to send `Twist` velocity messages
- A **service server** on `/draw_path` using `std_srvs/srv/Trigger`
- A timed control loop that alternates between moving forward and turning 90 degrees, four times

### Build the image (includes the package)

```bash
docker build -t ros2-humble-turtlesim .
```

Colcon builds the `turtle_magic` package automatically during the image build.

### Run turtlesim

```bash
open -a XQuartz && xhost + 127.0.0.1

docker run -d \
  --name ros2_turtlesim \
  -e DISPLAY=host.docker.internal:0 \
  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
  ros2-humble-turtlesim \
  bash -c "source /opt/ros/humble/setup.bash && source /ros2_ws/install/setup.bash && ros2 run turtlesim turtlesim_node"
```

### Reset the turtle to center (so the square fits on screen)

```bash
docker exec ros2_turtlesim bash -c \
  "source /opt/ros/humble/setup.bash && ros2 service call /reset std_srvs/srv/Empty"
```

### Start the path_drawer node (in a separate terminal)

```bash
docker exec -it ros2_turtlesim bash -c \
  "source /opt/ros/humble/setup.bash && source /ros2_ws/install/setup.bash && ros2 run turtle_magic path_drawer"
```

You will see: `PathDrawer ready. Call /draw_path to draw a square.`

### Press the magic button (in another terminal)

```bash
docker exec ros2_turtlesim bash -c \
  "source /opt/ros/humble/setup.bash && ros2 service call /draw_path std_srvs/srv/Trigger"
```

The turtle will draw a square (about 14 seconds). The service returns:

```
response: std_srvs.srv.Trigger_Response(success=True, message='Square complete!')
```
