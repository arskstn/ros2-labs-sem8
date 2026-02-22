#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
import math
from math import pi

'''
используется абсолютная позиция по варианту 3.

TODO: углы нормализовать [-pi;+pi] надо - некритично, просто она будет двигаться на 350 градусов вместо 10 против часовой стрелки если потребуется
при движении от второй вершины к начальной (третьей) затычка для угла стоит - сломает логику если начальная тетта != 0
'''

#let smaller angle be 30 degrees. can be changed

class TurtleFigureTriangle(Node):
    def pose_callback(self, msg):
        x = msg.x
        y = msg.y
        theta = msg.theta
        linear_vel = msg.linear_velocity
        angular_vel = msg.angular_velocity
            
        self.current_x = msg.x
        self.current_y = msg.y
        self.current_theta = msg.theta
            
        self.get_logger().info(f'Position: x={x:.2f}, y={y:.2f}, theta={theta:.2f}')
        
    def __init__(self):
        super().__init__('turtle_figure_triangle')
        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
            
        self.subscription = self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.subscription  # предотвратить предупреждение о неиспользуемой переменной

        self.initial_x = 5.544444561004639
        self.initial_y = 5.544444561004639
        self.initial_theta = 0.0
        
        self.current_x = self.initial_x
        self.current_y = self.initial_y
        self.current_theta = self.initial_theta
        
        self.linear_speed = 1.0 #m/s
        self.angular_speed = 1.0 #rad/s
        self.smaller_angle_deg = 30 #can be changed!!!
        self.smaller_angle = pi - math.radians(self.smaller_angle_deg)
        self.bigger_angle = pi - math.radians(180-90-self.smaller_angle_deg)
        
        self.smaller_leg_time = 2 #can be changed. affects hypot and second leg length
        self.smaller_leg_length = self.smaller_leg_time * self.linear_speed
        self.smaller_angle_time = self.smaller_angle/self.angular_speed
        
        self.hypot_time = (self.smaller_leg_length / math.cos(pi + self.smaller_angle)) / self.linear_speed
        self.hypot_length = self.hypot_time * self.linear_speed
        
        self.bigger_angle_time = self.bigger_angle/self.angular_speed
        self.bigger_leg_length = abs(self.smaller_leg_length * math.tan(pi + self.smaller_angle))
        self.bigger_leg_time = self.bigger_leg_length * self.linear_speed
        
        self.reset_angle_time = (2*pi - self.bigger_angle - self.smaller_angle)/self.angular_speed
        

        self.twist_msg = Twist()

        self.timer_period = 0.01
        self.timer = self.create_timer(self.timer_period, self.move_turtle)

        self.start_time = self.get_clock().now().nanoseconds / 1e9
        self.state = 1
        
        # self.initial_x = 5.544444561004639
        # self.initial_y = 5.544444561004639
        # self.initial_theta = 0.0
        
        #calculating verteces
        self.goal_x_1 = self.initial_x + self.smaller_leg_length
        self.goal_y_1 = self.initial_y
        self.goal_theta_1 = self.smaller_angle #150 deg (180-30)
        self.goal_x_2 = self.initial_x # + self.hypot_length * math.cos(math.radians(self.smaller_angle_deg)) - надо ли? х этой вершины будет на одной линией со стартом
        self.goal_y_2 = self.initial_y + math.sin(math.radians(self.smaller_angle_deg)) * self.hypot_length
        self.goal_theta_2 = -pi/2 #затычка, но для меньшего угла = 30 градусов работает. по идее и дальше должна работать тк мы тупо в начало пойдем. Сломается если стартовая тетта не ноль, думаю
        self.goal_x_3 = self.initial_x
        self.goal_y_3 = self.initial_y
        self.goal_theta_3 = 0.0
        
        #дорогому слушателю по имени N посвящается:
        #а зачем ты сначала от пи отнимаешь угол в опеределении? чтобы по внутренним ездить углам а не по внешним
        #а почему ты тут math.radians берешь от угла который кидал в градусы специально. потому что лев не заботит себя проблемами излишних вычислений. а вводить клон угла без учета пи мне лень. сам сделай кинь PR, я лабы спидраню
        
        self.epsilon = 0.05 #allowed error for distance measurement
        self.angle_epsilon = 0.05 #allowed error for angle measurement
        

    def move_turtle(self):
        current_time = self.get_clock().now().nanoseconds / 1e9
        elapsed = current_time - self.start_time
        
        #вывод достижения вершин

        if self.state == 1:
            self.get_logger().info(f'Moving to: x={self.goal_x_1:.2f}, y={self.goal_y_1:.2f}')
        
            dx = self.goal_x_1 - self.current_x
            dy = self.goal_y_1 - self.current_y
            distance = (dx**2 + dy**2)**(1/2)
            
            if distance > self.epsilon:
                self.twist_msg.linear.x = self.linear_speed
                self.twist_msg.angular.z = 0.0
            else:
                self.get_logger().info(f'VERTIX 1 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.state = 2
                self.twist_msg.linear.x = 0.0

        elif self.state == 2:
            self.get_logger().info(f'Moving to: theta={self.goal_theta_1:.2f}')
            angle_error = self.goal_theta_1 - self.current_theta
            
            if abs(angle_error) > self.epsilon:
                self.twist_msg.angular.z = self.angular_speed
            else:
                self.state = 3
                self.twist_msg.angular.z = 0.0
                
        elif self.state == 3:
            self.get_logger().info(f'Moving to: x={self.goal_x_2:.2f}, y={self.goal_y_2:.2f}')
            dx = self.goal_x_2 - self.current_x
            dy = self.goal_y_2 - self.current_y
            distance = (dx**2 + dy**2)**(1/2)
            
            if distance > self.epsilon:
                self.twist_msg.linear.x = self.linear_speed
                self.twist_msg.angular.z = 0.0
            else:
                self.get_logger().info(f'VERTIX 2 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.state = 4
                self.twist_msg.linear.x = 0.0
                
        elif self.state == 4:
            self.get_logger().info(f'Moving to: theta={self.goal_theta_2:.2f}')
            angle_error = self.goal_theta_2 - self.current_theta
            
            if abs(angle_error) > self.epsilon:
                self.twist_msg.angular.z = self.angular_speed
            else:
                self.state = 5
                self.twist_msg.angular.z = 0.0
                
        elif self.state == 5:
            self.get_logger().info(f'Moving to: x={self.goal_x_3:.2f}, y={self.goal_y_3:.2f}')
            dx = self.goal_x_3 - self.current_x
            dy = self.goal_y_3 - self.current_y
            distance = (dx**2 + dy**2)**(1/2)
            
            if distance > self.epsilon:
                self.twist_msg.linear.x = self.linear_speed
                self.twist_msg.angular.z = 0.0
            else:
                self.get_logger().info(f'VERTIX 3 REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.state = 6
                self.twist_msg.linear.x = 0.0
        
        else:
            self.get_logger().info(f'Moving to: theta={self.goal_theta_3:.2f}')
            angle_error = self.goal_theta_3 - self.current_theta
            
            if abs(angle_error) > self.epsilon:
                self.twist_msg.angular.z = self.angular_speed
            else:
                self.get_logger().info(f'INITIAL POSITION REACHED!!!!!!!!!!!!!!!!!!!!!!')
                self.get_logger().info(f'stopping!')
                self.twist_msg.linear.x = 0.0
                self.twist_msg.angular.z = 0.0
       
        self.publisher_.publish(self.twist_msg)
        # self.get_logger().info(
        #     f'Publishing velocity: linear={self.twist_msg.linear.x:.2f}, '
        #     f'angular={self.twist_msg.angular.z:.2f}, state={self.state}'
        # )

def main(args=None):
    rclpy.init(args=args)
    node = TurtleFigureTriangle()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
