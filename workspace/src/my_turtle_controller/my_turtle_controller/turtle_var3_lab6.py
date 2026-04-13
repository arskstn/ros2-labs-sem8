#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
import math
from math import pi

'''
лаб 6, вариант 3: параметры задают координаты вершин фигуры.
базируется на лаб 3 (управление по положению).
углы поворота вычисляются через atan2 от координат вершин, а не хардкодятся —
это позволяет задавать произвольный треугольник, а не только заданный углами варианта.
нормализация угла [-pi; pi] добавлена чтобы черепаха крутилась в ближайшую сторону.
'''

#let smaller angle be 30 degrees. default vertices match lab3

class TurtleFigureTriangleLab6(Node):
    def pose_callback(self, msg):
        self.current_x = msg.x
        self.current_y = msg.y
        self.current_theta = msg.theta
        self.get_logger().info(f'Position: x={msg.x:.2f}, y={msg.y:.2f}, theta={msg.theta:.2f}')

    def __init__(self):
        super().__init__('turtle_figure_triangle_lab6')

        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.subscription = self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.subscription  # предотвратить предупреждение о неиспользуемой переменной

        self.initial_x = 5.544444561004639
        self.initial_y = 5.544444561004639
        self.initial_theta = 0.0

        self.current_x = self.initial_x
        self.current_y = self.initial_y
        self.current_theta = self.initial_theta

        #параметры: координаты вершин треугольника. дефолты соответствуют лаб 3
        self.declare_parameter('vertex1_x', self.initial_x + 2.0)
        self.declare_parameter('vertex1_y', self.initial_y)
        self.declare_parameter('vertex2_x', self.initial_x)
        self.declare_parameter('vertex2_y', self.initial_y + 1.154)  #sin(30)*hypot из лаб 3

        self.goal_x_1 = self.get_parameter('vertex1_x').value
        self.goal_y_1 = self.get_parameter('vertex1_y').value
        self.goal_x_2 = self.get_parameter('vertex2_x').value
        self.goal_y_2 = self.get_parameter('vertex2_y').value
        self.goal_x_3 = self.initial_x
        self.goal_y_3 = self.initial_y

        self.get_logger().info(
            f'Vertices: '
            f'V1=({self.goal_x_1:.2f}, {self.goal_y_1:.2f}), '
            f'V2=({self.goal_x_2:.2f}, {self.goal_y_2:.2f}), '
            f'V3=({self.goal_x_3:.2f}, {self.goal_y_3:.2f})'
        )

        #углы поворота вычисляются из координат вершин через atan2
        self.heading_to_v1 = math.atan2(self.goal_y_1 - self.initial_y, self.goal_x_1 - self.initial_x)
        self.heading_to_v2 = math.atan2(self.goal_y_2 - self.goal_y_1, self.goal_x_2 - self.goal_x_1)
        self.heading_to_v3 = math.atan2(self.goal_y_3 - self.goal_y_2, self.goal_x_3 - self.goal_x_2)

        self.linear_speed = 1.0  #m/s
        self.angular_speed = 1.0  #rad/s

        self.epsilon = 0.15  #allowed error for distance measurement
        self.angle_epsilon = 0.05  #allowed error for angle measurement

        self.twist_msg = Twist()
        self.timer_period = 0.01
        self.timer = self.create_timer(self.timer_period, self.move_turtle)
        self.state = 1

    def normalize_angle(self, angle):
        #нормализация в [-pi; pi] чтобы крутиться в ближайшую сторону
        while angle > pi:
            angle -= 2 * pi
        while angle < -pi:
            angle += 2 * pi
        return angle

    def turn_to(self, target_theta):
        #возвращает angular.z и True если угол достигнут
        error = self.normalize_angle(target_theta - self.current_theta)
        if abs(error) > self.angle_epsilon:
            self.twist_msg.angular.z = self.angular_speed if error > 0 else -self.angular_speed
            return False
        else:
            self.twist_msg.angular.z = 0.0
            return True

    def move_to(self, goal_x, goal_y):
        #возвращает linear.x и True если точка достигнута
        dx = goal_x - self.current_x
        dy = goal_y - self.current_y
        distance = (dx**2 + dy**2)**(1/2)
        if distance > self.epsilon:
            self.twist_msg.linear.x = self.linear_speed
            self.twist_msg.angular.z = 0.0
            return False
        else:
            self.twist_msg.linear.x = 0.0
            return True

    def move_turtle(self):
        if self.state == 1:
            self.get_logger().info(f'Turning to face V1: theta={self.heading_to_v1:.2f}')
            if self.turn_to(self.heading_to_v1):
                self.state = 2

        elif self.state == 2:
            self.get_logger().info(f'Moving to: x={self.goal_x_1:.2f}, y={self.goal_y_1:.2f}')
            if self.move_to(self.goal_x_1, self.goal_y_1):
                self.get_logger().info('VERTIX 1 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.state = 3

        elif self.state == 3:
            self.get_logger().info(f'Turning to face V2: theta={self.heading_to_v2:.2f}')
            if self.turn_to(self.heading_to_v2):
                self.state = 4

        elif self.state == 4:
            self.get_logger().info(f'Moving to: x={self.goal_x_2:.2f}, y={self.goal_y_2:.2f}')
            if self.move_to(self.goal_x_2, self.goal_y_2):
                self.get_logger().info('VERTIX 2 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.state = 5

        elif self.state == 5:
            self.get_logger().info(f'Turning to face V3: theta={self.heading_to_v3:.2f}')
            if self.turn_to(self.heading_to_v3):
                self.state = 6

        elif self.state == 6:
            self.get_logger().info(f'Moving to: x={self.goal_x_3:.2f}, y={self.goal_y_3:.2f}')
            if self.move_to(self.goal_x_3, self.goal_y_3):
                self.get_logger().info('VERTIX 3 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.state = 7

        else:
            self.get_logger().info(f'Turning to: theta={self.initial_theta:.2f}')
            if self.turn_to(self.initial_theta):
                self.get_logger().info('INITIAL POSITION REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.get_logger().info('stopping!')
                self.twist_msg.linear.x = 0.0
                self.twist_msg.angular.z = 0.0

        self.publisher_.publish(self.twist_msg)


def main(args=None):
    rclpy.init(args=args)
    node = TurtleFigureTriangleLab6()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
