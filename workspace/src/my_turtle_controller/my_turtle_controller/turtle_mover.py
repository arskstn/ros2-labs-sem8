#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class TurtleMover(Node):
    def __init__(self):
        super().__init__('turtle_mover')
        # Создаем паблишера (publisher) в топик /turtle1/cmd_vel с типом сообщения Twist длиной очереди 10 сообщений
        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        # Таймер срабатывает каждые 0.5 секунды (2 раза в секунду)
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.move_turtle)
        # Создадим сообщение Twist один раз и будем публиковать его каждый таймерный тик
        self.twist_msg = Twist()
        self.twist_msg.linear.x = 2.0  # скорость по оси x
        self.twist_msg.angular.z = 1.0 # угловая скорость вокруг z

    def move_turtle(self):
        # Публикуем сообщение с заданными скоростями
        self.publisher_.publish(self.twist_msg)
        self.get_logger().info('Publishing turtle velocity: linear=%f, angular=%f' %
                                (self.twist_msg.linear.x, self.twist_msg.angular.z))

def main(args=None):
    rclpy.init(args=args)
    node = TurtleMover()
    rclpy.spin(node)

    # По завершении
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
