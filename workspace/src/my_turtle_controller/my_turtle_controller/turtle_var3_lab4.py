#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtlesim.srv import SetPen
from std_srvs.srv import Empty
import math
from math import pi


PEN_STRAIGHT_COLORS = [
    (255, 255, 255, 4, 0),  # white
    (80,  255,  80, 4, 0),  # green
]
PEN_OFF = (0, 0, 0, 1, 1)  # перо выключено во время поворота


class TurtleFigureTriangleLab4(Node):
    def pose_callback(self, msg):
        self.current_x = msg.x
        self.current_y = msg.y
        self.current_theta = msg.theta
        self.get_logger().info(f'Position: x={msg.x:.2f}, y={msg.y:.2f}, theta={msg.theta:.2f}')

    def __init__(self):
        super().__init__('turtle_figure_triangle_lab4')

        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.subscription = self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.subscription  # kill unused var warnings

        self.reset_client = self.create_client(Empty, '/reset')
        self.set_pen_client = self.create_client(SetPen, '/turtle1/set_pen')

        self.initial_x = 5.544444561004639
        self.initial_y = 5.544444561004639
        self.initial_theta = 0.0

        self.current_x = self.initial_x
        self.current_y = self.initial_y
        self.current_theta = self.initial_theta

        self.linear_speed = 1.0  #m/s
        self.angular_speed = 1.0  #rad/s
        self.smaller_angle_deg = 30  #can be changed!!!
        self.smaller_angle = pi - math.radians(self.smaller_angle_deg)
        self.bigger_angle = pi - math.radians(180 - 90 - self.smaller_angle_deg)

        self.smaller_leg_time = 2  #can be changed. affects hypot and second leg length
        self.smaller_leg_length = self.smaller_leg_time * self.linear_speed
        self.smaller_angle_time = self.smaller_angle / self.angular_speed

        self.hypot_time = (self.smaller_leg_length / math.cos(pi + self.smaller_angle)) / self.linear_speed
        self.hypot_length = self.hypot_time * self.linear_speed

        self.bigger_angle_time = self.bigger_angle / self.angular_speed
        self.bigger_leg_length = abs(self.smaller_leg_length * math.tan(pi + self.smaller_angle))
        self.bigger_leg_time = self.bigger_leg_length * self.linear_speed

        self.reset_angle_time = (2 * pi - self.bigger_angle - self.smaller_angle) / self.angular_speed

        #calculating verteces
        self.goal_x_1 = self.initial_x + self.smaller_leg_length
        self.goal_y_1 = self.initial_y
        self.goal_theta_1 = self.smaller_angle  #150 deg (180-30)
        self.goal_x_2 = self.initial_x
        self.goal_y_2 = self.initial_y + math.sin(math.radians(self.smaller_angle_deg)) * self.hypot_length
        self.goal_theta_2 = -pi / 2  #angle=30 stub can be changed
        self.goal_x_3 = self.initial_x
        self.goal_y_3 = self.initial_y
        self.goal_theta_3 = 0.0

        self.epsilon = 0.15  #allowed error for distance measurement
        self.angle_epsilon = 0.05  #allowed error for angle measurement

        self.twist_msg = Twist()
        self.timer_period = 0.01
        self.timer = self.create_timer(self.timer_period, self.move_turtle)
        self.start_time = self.get_clock().now().nanoseconds / 1e9
        self.state = 1

        self.is_turning = False
        self.straight_color_index = 0
        self.home_reached_time = None

        self.call_reset()
        self.set_pen(*PEN_STRAIGHT_COLORS[self.straight_color_index])

    def call_reset(self):
        if not self.reset_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().warn('/reset service not available')
            return
        self.reset_client.call_async(Empty.Request())
        self.get_logger().info('Reset called.')

    def set_pen(self, r, g, b, width, off):
        if not self.set_pen_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn('/turtle1/set_pen service not available')
            return
        req = SetPen.Request()
        req.r = r
        req.g = g
        req.b = b
        req.width = width
        req.off = off
        self.set_pen_client.call_async(req)

    def update_pen_for_direction(self, turning: bool):
        if turning == self.is_turning:
            return
        self.is_turning = turning
        if turning:
            self.set_pen(*PEN_OFF)
            self.get_logger().info('Turning: pen off')
        else:
            self.straight_color_index = (self.straight_color_index + 1) % len(PEN_STRAIGHT_COLORS)
            self.set_pen(*PEN_STRAIGHT_COLORS[self.straight_color_index])
            self.get_logger().info(f'Straight: pen color {self.straight_color_index}')

    def move_turtle(self):
        current_time = self.get_clock().now().nanoseconds / 1e9

        if self.home_reached_time is not None:
            if current_time - self.home_reached_time >= 60.0:
                self.get_logger().info('60s elapsed, resetting!')
                self.call_reset()
                self.state = 1
                self.home_reached_time = None
                self.straight_color_index = 0
                self.set_pen(*PEN_STRAIGHT_COLORS[self.straight_color_index])
                self.is_turning = False
                return

        if self.state == 1:
            self.get_logger().info(f'Moving to: x={self.goal_x_1:.2f}, y={self.goal_y_1:.2f}')
            dx = self.goal_x_1 - self.current_x
            dy = self.goal_y_1 - self.current_y
            distance = (dx**2 + dy**2)**(1/2)

            self.update_pen_for_direction(turning=False)

            if distance > self.epsilon:
                self.twist_msg.linear.x = self.linear_speed
                self.twist_msg.angular.z = 0.0
            else:
                self.get_logger().info('VERTIX 1 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.state = 2
                self.twist_msg.linear.x = 0.0

        elif self.state == 2:
            self.get_logger().info(f'Moving to: theta={self.goal_theta_1:.2f}')
            angle_error = self.goal_theta_1 - self.current_theta

            self.update_pen_for_direction(turning=True)

            if abs(angle_error) > self.angle_epsilon:
                self.twist_msg.angular.z = self.angular_speed
            else:
                self.state = 3
                self.twist_msg.angular.z = 0.0

        elif self.state == 3:
            self.get_logger().info(f'Moving to: x={self.goal_x_2:.2f}, y={self.goal_y_2:.2f}')
            dx = self.goal_x_2 - self.current_x
            dy = self.goal_y_2 - self.current_y
            distance = (dx**2 + dy**2)**(1/2)

            self.update_pen_for_direction(turning=False)

            if distance > self.epsilon:
                self.twist_msg.linear.x = self.linear_speed
                self.twist_msg.angular.z = 0.0
            else:
                self.get_logger().info('VERTIX 2 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.state = 4
                self.twist_msg.linear.x = 0.0

        elif self.state == 4:
            self.get_logger().info(f'Moving to: theta={self.goal_theta_2:.2f}')
            angle_error = self.goal_theta_2 - self.current_theta

            self.update_pen_for_direction(turning=True)

            if abs(angle_error) > self.angle_epsilon:
                self.twist_msg.angular.z = self.angular_speed
            else:
                self.state = 5
                self.twist_msg.angular.z = 0.0

        elif self.state == 5:
            dx = self.goal_x_3 - self.current_x
            dy = self.goal_y_3 - self.current_y
            distance = (dx**2 + dy**2)**(1/2)

            self.update_pen_for_direction(turning=False)

            if distance > self.epsilon:
                self.twist_msg.linear.x = self.linear_speed
                self.twist_msg.angular.z = 0.0
            else:
                self.get_logger().info('VERTIX 3 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.state = 6
                self.twist_msg.linear.x = 0.0

        else:
            self.get_logger().info(f'Moving to: theta={self.goal_theta_3:.2f}')
            angle_error = self.goal_theta_3 - self.current_theta

            self.update_pen_for_direction(turning=True)

            if abs(angle_error) > self.angle_epsilon:
                self.twist_msg.angular.z = self.angular_speed
            else:
                self.get_logger().info('INITIAL POSITION REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.get_logger().info('stopping!')
                self.twist_msg.linear.x = 0.0
                self.twist_msg.angular.z = 0.0
                if self.home_reached_time is None:
                    self.home_reached_time = current_time

        self.publisher_.publish(self.twist_msg)


def main(args=None):
    rclpy.init(args=args)
    node = TurtleFigureTriangleLab4()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
