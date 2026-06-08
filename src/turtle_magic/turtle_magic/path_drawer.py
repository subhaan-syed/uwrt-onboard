#!/usr/bin/env python3

# path_drawer.py
# This node is the "magic button." It waits for a service call, and when
# triggered, it drives the turtle in a square by publishing velocity commands.
#
# Core ROS2 concepts used here:
#   Publisher  - sends messages on a topic (we publish Twist to /turtle1/cmd_vel)
#   Service    - a request/response mechanism (we advertise /draw_path)
#   Twist msg  - the standard ROS2 type for velocity: linear (x/y/z) and angular (x/y/z)

import math
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist       # velocity command message
from std_srvs.srv import Trigger          # simple service: no input, returns success + message


# How fast to drive each side of the square (turtlesim units per second)
LINEAR_SPEED = 1.5

# How long to drive forward for each side (seconds)
# Side length = LINEAR_SPEED * SIDE_DURATION = 1.5 * 2.0 = 3.0 units
SIDE_DURATION = 2.0

# Turning speed in radians per second.
# pi/2 rad/s means one full 90-degree turn takes exactly 1 second.
ANGULAR_SPEED = math.pi / 2

# How long to turn for each corner (seconds)
# Angle turned = ANGULAR_SPEED * TURN_DURATION = (pi/2) * 1.0 = pi/2 rad = 90 degrees
TURN_DURATION = 1.0


class PathDrawer(Node):

    def __init__(self):
        # Initialise this node with the name 'path_drawer'.
        # Every ROS2 node needs a unique name so other nodes can find it.
        super().__init__('path_drawer')

        # Create a publisher on the /turtle1/cmd_vel topic.
        # The second argument is the message type (Twist).
        # The third argument (10) is the queue size -- how many messages to
        # buffer if the subscriber is slow.
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        # Advertise the /draw_path service using the Trigger service type.
        # Trigger takes no input and returns: bool success, string message.
        # When someone calls this service, draw_path_callback runs.
        self.service = self.create_service(
            Trigger, 'draw_path', self.draw_path_callback
        )

        self.get_logger().info('PathDrawer ready. Call /draw_path to draw a square.')

    def publish_velocity(self, linear_x, angular_z, duration):
        """
        Publish a constant velocity command for a fixed amount of time, then stop.

        linear_x  -- forward/backward speed (positive = forward)
        angular_z -- rotation speed in rad/s (positive = counter-clockwise / left turn)
        duration  -- how many seconds to keep publishing this command
        """
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z

        # Send the command repeatedly at ~10 Hz for the full duration.
        # Publishing once and waiting would work too, but looping at 10 Hz
        # is more realistic and keeps the turtle moving smoothly.
        end_time = time.time() + duration
        while time.time() < end_time:
            self.publisher.publish(msg)
            time.sleep(0.1)

        # Send a zero-velocity message to bring the turtle to a full stop
        # before the next motion segment begins.
        self.publisher.publish(Twist())
        time.sleep(0.2)

    def draw_path_callback(self, request, response):
        """
        Service callback -- runs when /draw_path is called.

        Drives the turtle in a square:
          - Move forward 3 units (1.5 m/s for 2 s)
          - Turn left 90 degrees (pi/2 rad/s for 1 s)
          - Repeat 4 times to close the square

        The square fits comfortably inside the turtlesim window as long as
        the turtle starts near the center. Call /reset before this service
        to guarantee a clean starting position.
        """
        self.get_logger().info('Starting square path...')

        for side in range(4):
            self.get_logger().info(f'Side {side + 1} of 4')

            # Drive forward along one side of the square
            self.publish_velocity(LINEAR_SPEED, 0.0, SIDE_DURATION)

            # Turn left 90 degrees to face the next side
            self.publish_velocity(0.0, ANGULAR_SPEED, TURN_DURATION)

        self.get_logger().info('Square complete!')

        # Fill in the service response
        response.success = True
        response.message = 'Square complete!'
        return response


def main(args=None):
    rclpy.init(args=args)
    node = PathDrawer()

    # spin() keeps the node alive and processes incoming service calls.
    # Without this, the node would exit immediately.
    rclpy.spin(node)

    rclpy.shutdown()


if __name__ == '__main__':
    main()
