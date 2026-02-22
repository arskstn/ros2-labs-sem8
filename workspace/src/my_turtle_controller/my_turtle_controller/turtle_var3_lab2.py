#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math
from math import pi

#let smaller angle be 30 degrees. can be changed

class TurtleFigureTriangle(Node):
    def __init__(self):
        super().__init__('turtle_figure_triangle')
        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        
        self.linear_speed = 1.0 #m/s
        self.angular_speed = 2.0 #rad/s
        self.smaller_angle_deg = 23 #can be changed!!!
        self.smaller_angle = pi - math.radians(self.smaller_angle_deg)
        self.bigger_angle = pi - math.radians(180-90-self.smaller_angle_deg)
        
        self.smaller_leg_time = 2 #can be changed. affects hypot and second leg length
        self.smaller_leg_length = self.smaller_leg_time * self.linear_speed
        self.smaller_angle_time = self.smaller_angle/self.angular_speed
        
        self.hypot_time = (self.smaller_leg_length / math.cos(pi + self.smaller_angle)) / self.linear_speed
        
        self.bigger_angle_time = self.bigger_angle/self.angular_speed
        self.bigger_leg_time = abs(self.smaller_leg_length * math.tan(pi + self.smaller_angle)) * self.linear_speed
        
        self.reset_angle_time = (2*pi - self.bigger_angle - self.smaller_angle)/self.angular_speed
        
        

        self.twist_msg = Twist()

        self.timer_period = 0.01
        self.timer = self.create_timer(self.timer_period, self.move_turtle)

        self.start_time = self.get_clock().now().nanoseconds / 1e9
        self.state = 1

    def move_turtle(self):
        current_time = self.get_clock().now().nanoseconds / 1e9
        elapsed = current_time - self.start_time

        if self.state == 1:
            self.twist_msg.linear.x = self.linear_speed
            self.twist_msg.angular.z = 0.0

            if elapsed > self.smaller_leg_time:
                self.state = 2
                self.start_time = current_time

        elif self.state == 2:
            self.twist_msg.linear.x = 0.0
            self.twist_msg.angular.z = self.angular_speed

            if elapsed > self.smaller_angle_time:
                self.state = 3
                self.start_time = current_time
                
        elif self.state == 3:
            self.twist_msg.linear.x = self.linear_speed
            self.twist_msg.angular.z = 0.0

            if elapsed > self.hypot_time:
                self.state = 4
                self.start_time = current_time
        
        elif self.state == 4:
            self.twist_msg.linear.x = 0.0
            self.twist_msg.angular.z = self.angular_speed

            if elapsed > self.bigger_angle_time:
                self.state = 5
                self.start_time = current_time
        
        elif self.state == 5:
            self.twist_msg.linear.x = self.linear_speed
            self.twist_msg.angular.z = 0.0

            if elapsed > self.bigger_leg_time:
                self.state = 6
                self.start_time = current_time
        
        else:
            self.twist_msg.linear.x = 0.0
            self.twist_msg.angular.z = self.angular_speed
            
            if elapsed > self.reset_angle_time:
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
