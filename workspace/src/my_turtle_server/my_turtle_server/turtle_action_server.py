#!/usr/bin/env python3
import math
from math import pi

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose

#алгоритм управления по положению из лаб 3, траектория треугольника из лаб 1

from my_turtle_interface.action import DrawFigure


class TurtleActionServer(Node):
    def pose_callback(self, msg):
        self.current_x = msg.x
        self.current_y = msg.y
        self.current_theta = msg.theta

    def __init__(self):
        super().__init__('turtle_action_server')

        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.subscription = self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.subscription  # предотвратить предупреждение о неиспользуемой переменной

        self._action_server = ActionServer(self, DrawFigure, 'draw_figure', self.execute_callback)

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

        self.smaller_leg_length = 2 * self.linear_speed
        self.hypot_length = (self.smaller_leg_length / math.cos(pi + self.smaller_angle))
        self.bigger_leg_length = abs(self.smaller_leg_length * math.tan(pi + self.smaller_angle))

        #calculating verteces
        self.goal_x_1 = self.initial_x + self.smaller_leg_length
        self.goal_y_1 = self.initial_y
        self.goal_theta_1 = self.smaller_angle  #150 deg (180-30)
        self.goal_x_2 = self.initial_x
        self.goal_y_2 = self.initial_y + math.sin(math.radians(self.smaller_angle_deg)) * self.hypot_length
        self.goal_theta_2 = -pi / 2  #затычка для угла 30, работает тк идем в начало
        self.goal_x_3 = self.initial_x
        self.goal_y_3 = self.initial_y
        self.goal_theta_3 = 0.0

        self.epsilon = 0.15  #allowed error for distance measurement
        self.angle_epsilon = 0.05  #allowed error for angle measurement

        self.get_logger().info('Action server /draw_figure is up and running!')

    def stop(self):
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.publisher_.publish(twist)

    def execute_callback(self, goal_handle):
        self.get_logger().info('Goal received, starting mission...')

        feedback_msg = DrawFigure.Feedback()
        twist = Twist()
        rate = self.create_rate(100)  #100 Hz control loop
        state = 1

        while rclpy.ok():
            dx = dy = distance = angle_error = 0.0

            if state == 1:
                dx = self.goal_x_1 - self.current_x
                dy = self.goal_y_1 - self.current_y
                distance = (dx**2 + dy**2)**(1/2)
                if distance > self.epsilon:
                    twist.linear.x = self.linear_speed
                    twist.angular.z = 0.0
                else:
                    self.get_logger().info('VERTIX 1 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                    feedback_msg.vertex_reached = 1
                    feedback_msg.status = 'Vertex 1 reached'
                    goal_handle.publish_feedback(feedback_msg)
                    twist.linear.x = 0.0
                    state = 2

            elif state == 2:
                angle_error = self.goal_theta_1 - self.current_theta
                if abs(angle_error) > self.angle_epsilon:
                    twist.angular.z = self.angular_speed
                else:
                    twist.angular.z = 0.0
                    state = 3

            elif state == 3:
                dx = self.goal_x_2 - self.current_x
                dy = self.goal_y_2 - self.current_y
                distance = (dx**2 + dy**2)**(1/2)
                if distance > self.epsilon:
                    twist.linear.x = self.linear_speed
                    twist.angular.z = 0.0
                else:
                    self.get_logger().info('VERTIX 2 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                    feedback_msg.vertex_reached = 2
                    feedback_msg.status = 'Vertex 2 reached'
                    goal_handle.publish_feedback(feedback_msg)
                    twist.linear.x = 0.0
                    state = 4

            elif state == 4:
                angle_error = self.goal_theta_2 - self.current_theta
                if abs(angle_error) > self.angle_epsilon:
                    twist.angular.z = self.angular_speed
                else:
                    twist.angular.z = 0.0
                    state = 5

            elif state == 5:
                dx = self.goal_x_3 - self.current_x
                dy = self.goal_y_3 - self.current_y
                distance = (dx**2 + dy**2)**(1/2)
                if distance > self.epsilon:
                    twist.linear.x = self.linear_speed
                    twist.angular.z = 0.0
                else:
                    self.get_logger().info('VERTIX 3 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                    feedback_msg.vertex_reached = 3
                    feedback_msg.status = 'Vertex 3 reached'
                    goal_handle.publish_feedback(feedback_msg)
                    twist.linear.x = 0.0
                    state = 6

            elif state == 6:
                angle_error = self.goal_theta_3 - self.current_theta
                if abs(angle_error) > self.angle_epsilon:
                    twist.angular.z = self.angular_speed
                else:
                    self.stop()
                    break

            self.publisher_.publish(twist)
            rate.sleep()

        self.get_logger().info('INITIAL POSITION REACHED!!!!!!!!!!!!!!!!!!!!!!')
        self.get_logger().info('Mission complete!')

        goal_handle.succeed()
        result = DrawFigure.Result()
        result.success = True
        result.message = 'Mission complete: triangle finished, back at initial position'
        return result


def main(args=None):
    rclpy.init(args=args)
    node = TurtleActionServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
