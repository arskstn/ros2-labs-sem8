#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from turtlesim.msg import Pose  # Тип Pose из turtlesim

class TurtlePoseFollower(Node):
    def __init__(self):
        super().__init__('turtle_pose_follower')

        # Подписчик на /turtle1/pose
        self.pose_subscriber = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10
        )

        # Издатель в топик /turtle1/cmd_vel
        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        
        # Текущая поза черепашки
        self.current_pose = Pose()

        # Таймер управления (10 Гц = 0.1 сек)
        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.control_loop)

        # Цель (перезаполняется каждый раз через set_goal)
        self.x_goal = 0.0
        self.y_goal = 0.0

        # Коэффициенты «П»-регулятора
        self.linear_k = 1.0
        self.angular_k = 4.0

        # Порог «прибыли» к цели
        self.arrival_tolerance = 0.01

        # Флаги состояния
        self.reached = False
        self.unreachable = False

        # Переменные для отслеживания «застрявшей» черепашки
        self.last_distance = float('inf')
        self.last_progress_time = self.get_clock().now().nanoseconds
        self.no_progress_limit = 2.0  # 2 секунды без движения— объявляем недостижимость

    def set_goal(self, x, y):
        """Задать новую цель и сбросить состояние."""
        self.x_goal = x
        self.y_goal = y

        self.reached = False
        self.unreachable = False

        self.last_distance = float('inf')
        self.last_progress_time = self.get_clock().now().nanoseconds

    def pose_callback(self, msg: Pose):
        """Сохранить текущую позу черепашки."""
        self.current_pose = msg

    def control_loop(self):
        """
        Вызывается таймером каждые 0.1 сек.
        Управляет движением к цели или определяет, что цель недостижима.
        """
        # Если уже «финиш» или «застряли», ничего не делаем:
        if self.reached or self.unreachable:
            return

        # Вычисляем расстояние до цели
        dx = self.x_goal - self.current_pose.x
        dy = self.y_goal - self.current_pose.y
        distance = math.sqrt(dx*dx + dy*dy)

        # Проверяем, достигли ли мы цели
        if distance < self.arrival_tolerance:
            self.stop_moving()
            self.reached = True
            self.get_logger().info('Goal reached! Stopping.')
            return

        # Проверяем, есть ли прогресс(движение). Смотрим на уменьшение distance
        current_time = self.get_clock().now().nanoseconds
        if distance < self.last_distance - 0.001:
            # Считаем, что движение есть, обновим метки
            self.last_progress_time = current_time
            self.last_distance = distance
        else:
            # Движения нет. Сколько прошло времени?
            time_no_progress = (current_time - self.last_progress_time) / 1e9
            if time_no_progress > self.no_progress_limit:
                # Долго стоим (или крутимся на месте) без движения — объявляем недостижимость
                self.stop_moving()
                self.unreachable = True
                self.get_logger().warn('Goal is unreachable! Stopping.')
                return

        # Управление по «П»-регулятору
        desired_angle = math.atan2(dy, dx)
        # Считаем угол вектора в заданной точке
        angle_error = desired_angle - self.current_pose.theta
        # Находим ошибку - разницу между углом черепахи и вектором

        # Нормализуем угол в диапазон [-pi, pi]. Чтобы поворачиваться в ближайшую сторону
        angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))

        # Формируем Twist
        twist = Twist()

        # Линейная скорость (ограничиваем сверху)
        twist.linear.x = self.linear_k * distance
        if twist.linear.x > 2.0:
            twist.linear.x = 2.0

        # Угловая скорость (аналогично ограничиваем)
        twist.angular.z = self.angular_k * angle_error
        if twist.angular.z > 2.0:
            twist.angular.z = 2.0
        elif twist.angular.z < -2.0:
            twist.angular.z = -2.0

        # Публикуем
        self.publisher_.publish(twist)

    def stop_moving(self):
        """Опубликовать нулевые скорости (остановка)."""
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.publisher_.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = TurtlePoseFollower()

    try:
        while rclpy.ok():
            # Запрашиваем у пользователя координаты цели
            user_input = input("\nВведите x y (или q для выхода): ").strip()
            if not user_input:
                continue
            if user_input.lower() == 'q':
                print("Выход из программы.")
                break

            # Парсим координаты
            coords = user_input.split()
            if len(coords) < 2:
                print("Ошибка: введите 2 числа (x и y) или 'q' для выхода.")
                continue

            try:
                x_goal = float(coords[0])
                y_goal = float(coords[1])
            except ValueError:
                print("Ошибка: некорректные координаты.")
                continue

            # Устанавливаем цель в ноду
            node.set_goal(x_goal, y_goal)
            node.get_logger().info(
                f'Идём к точке (x={x_goal:.2f}, y={y_goal:.2f})...'
            )

            # Пока не достигли цели и не объявили недостижимой — «крутим» ноду
            while rclpy.ok() and not node.reached and not node.unreachable:
                rclpy.spin_once(node, timeout_sec=0.1)

            # Выводим результат
            if node.reached:
                print("Цель достигнута!")
            elif node.unreachable:
                print("Цель недостижима — остановка.")
            else:
                # Если вышли из цикла из-за rclpy.ok() == False
                print("ROS остановлен извне.")
                break

    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
