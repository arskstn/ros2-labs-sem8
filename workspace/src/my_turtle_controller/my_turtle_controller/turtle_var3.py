#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from math import pi

class TurtleFigureTriangle(Node):
    def __init__(self):
        super().__init__('turtle_figure_triangle')
        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        
        self.linear_speed = 1.0
        self.angular_speed = 1.5
        '''
        omega * time = 6.28
        1.5 * time = 6.28
        time = 4.187
        '''

        self.half_circle_time = 4.187

        self.twist_msg = Twist()

        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.move_turtle)

        self.start_time = self.get_clock().now().nanoseconds / 1e9
        self.state = 1

    def move_turtle(self):
        current_time = self.get_clock().now().nanoseconds / 1e9
        elapsed = current_time - self.start_time

        if self.state == 1:
            self.twist_msg.linear.x = self.linear_speed
            self.twist_msg.angular.z = self.angular_speed

            if elapsed > self.half_circle_time:
                self.state = 2
                self.start_time = current_time


        elif self.state == 2:
            self.twist_msg.linear.x = self.linear_speed
            self.twist_msg.angular.z = -self.angular_speed

            if elapsed > self.half_circle_time:
                self.state = 1
                self.start_time = current_time

        self.publisher_.publish(self.twist_msg)
        self.get_logger().info(
            f'Publishing velocity: linear={self.twist_msg.linear.x:.2f}, '
            f'angular={self.twist_msg.angular.z:.2f}, state={self.state}'
        )

def main(args=None):
    rclpy.init(args=args)
    node = TurtleFigureTriangle()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
