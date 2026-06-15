#!/usr/bin/env python3

# path_drawer.py
# This node is the "magic button." It waits for a service call, and when
# triggered, it drives the turtle in a square by publishing velocity commands.
#
# Core ROS2 concepts used here:
#   Publisher    - sends messages on a topic (we publish Twist to /turtle1/cmd_vel)
#   Service      - a request/response mechanism (we advertise /draw_path)
#   Timer        - calls a function at a fixed rate (drives our motion loop at 10 Hz)
#   State machine - tracks which phase of the square we are in
#   Twist msg    - the standard ROS2 type for velocity: linear (x/y/z) and angular (x/y/z)
#
# WHY a timer instead of time.sleep():
#   The ROS2 executor is single-threaded by default. Calling time.sleep() inside a
#   callback (like a service callback) freezes the executor for the entire sleep
#   duration -- no other callbacks, timers, or service calls can be processed.
#   On a real robot this would mean missed sensor data and an unresponsive system.
#   Using create_timer() instead lets the executor continue running normally while
#   the turtle moves: the timer fires every 0.1 s, checks the current state, and
#   publishes the appropriate velocity command for that tick only.

import math
from enum import Enum, auto

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

# How long to turn at each corner (seconds)
# Angle turned = ANGULAR_SPEED * TURN_DURATION = (pi/2) * 1.0 = pi/2 rad = 90 degrees
TURN_DURATION = 1.0

# How often the control timer fires (seconds). 10 Hz = 0.1 s per tick.
TIMER_PERIOD = 0.1


class State(Enum):
    """The four phases of the square-drawing sequence."""
    IDLE    = auto()   # waiting for a service call, timer does nothing
    MOVING  = auto()   # driving forward along one side
    TURNING = auto()   # rotating 90 degrees at a corner
    DONE    = auto()   # all four sides finished, send a stop command then go IDLE


class PathDrawer(Node):

    def __init__(self):
        # Initialise this node with the name 'path_drawer'.
        # Every ROS2 node needs a unique name so other nodes can find it.
        super().__init__('path_drawer')

        # Create a publisher on the /turtle1/cmd_vel topic.
        # Queue size 10 means up to 10 messages can wait if the subscriber is slow.
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        # Advertise the /draw_path service using the Trigger service type.
        # Trigger takes no input and returns: bool success, string message.
        # When someone calls this service, draw_path_callback runs.
        self.service = self.create_service(
            Trigger, 'draw_path', self.draw_path_callback
        )

        # The control timer drives the state machine at 10 Hz.
        # It fires every TIMER_PERIOD seconds regardless of what else the node is doing.
        self.timer = self.create_timer(TIMER_PERIOD, self.timer_callback)

        # State machine variables.
        self.state = State.IDLE
        self.side_count = 0          # how many sides (and turns) have been completed
        self.state_start_time = None # ROS2 clock time when the current state began

        self.get_logger().info('PathDrawer ready. Call /draw_path to draw a square.')

    # -------------------------------------------------------------------------
    # Service callback
    # -------------------------------------------------------------------------

    def draw_path_callback(self, request, response):
        """
        Called when /draw_path is triggered (the "magic button press").

        This callback returns IMMEDIATELY -- it does not wait for the turtle to
        finish. Instead it kicks off the state machine and lets the timer do
        the actual motion work. This keeps the executor fully responsive.
        """
        if self.state != State.IDLE:
            # Reject the call if a path is already in progress.
            response.success = False
            response.message = 'Already drawing a path, please wait.'
            return response

        # Start the sequence: first phase is MOVING (driving forward).
        self.side_count = 0
        self.state_start_time = self.get_clock().now()
        self.state = State.MOVING
        self.get_logger().info('Starting square path...')

        # Return immediately. The timer will handle all the actual movement.
        response.success = True
        response.message = 'Square path started.'
        return response

    # -------------------------------------------------------------------------
    # Timer callback -- the state machine
    # -------------------------------------------------------------------------

    def timer_callback(self):
        """
        Fires every 0.1 seconds. Checks the current state, publishes the
        appropriate velocity, and handles transitions between states.

        The flow for one complete square:
            IDLE -> MOVING -> TURNING -> MOVING -> TURNING -> ... (x4) -> DONE -> IDLE
        """
        if self.state == State.IDLE:
            # Nothing to do while waiting for a service call.
            return

        # How many seconds have passed since the current state started.
        elapsed = (self.get_clock().now() - self.state_start_time).nanoseconds / 1e9

        if self.state == State.MOVING:
            # Publish a forward velocity command for this tick.
            msg = Twist()
            msg.linear.x = LINEAR_SPEED
            self.publisher.publish(msg)

            # If we have been moving long enough to cover one side, switch to turning.
            if elapsed >= SIDE_DURATION:
                self.side_count += 1
                self.get_logger().info(f'Side {self.side_count} complete, turning...')
                self._enter_state(State.TURNING)

        elif self.state == State.TURNING:
            # Publish a left-turn velocity command for this tick.
            msg = Twist()
            msg.angular.z = ANGULAR_SPEED
            self.publisher.publish(msg)

            # If we have turned long enough for 90 degrees, move to the next phase.
            if elapsed >= TURN_DURATION:
                if self.side_count >= 4:
                    # All four sides and turns are done.
                    self._enter_state(State.DONE)
                else:
                    self.get_logger().info(f'Turn complete, starting side {self.side_count + 1}...')
                    self._enter_state(State.MOVING)

        elif self.state == State.DONE:
            # Send a zero-velocity stop command, then go back to IDLE.
            self.publisher.publish(Twist())
            self.state = State.IDLE
            self.get_logger().info('Square complete!')

    def _enter_state(self, new_state):
        """Transition to a new state and record when it started."""
        self.state = new_state
        self.state_start_time = self.get_clock().now()


def main(args=None):
    rclpy.init(args=args)
    node = PathDrawer()

    # spin() keeps the node alive and hands control to the executor.
    # The executor processes timer callbacks and incoming service calls.
    rclpy.spin(node)

    rclpy.shutdown()


if __name__ == '__main__':
    main()
