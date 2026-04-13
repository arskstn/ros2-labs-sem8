#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from turtlesim.srv import TeleportAbsolute
from std_srvs.srv import Empty

from my_turtle_interface.srv import SendToHome

'''
Сервер SendToHome: при вызове сервиса телепортирует черепашку в начальную позицию
и сбрасывает симулятор через /reset.
'''

INITIAL_X = 5.544444561004639
INITIAL_Y = 5.544444561004639
INITIAL_THETA = 0.0


class TurtleControlServer(Node):
    def __init__(self):
        super().__init__('turtle_control_server')

        # Сервис, который предоставляем клиентам
        self.srv = self.create_service(
            SendToHome,
            'send_to_home',
            self.handle_send_to_home
        )

        # Клиент для телепортации черепашки
        self.teleport_client = self.create_client(TeleportAbsolute, '/turtle1/teleport_absolute')

        # Клиент для сброса симулятора
        self.reset_client = self.create_client(Empty, '/reset')

        self.get_logger().info('Service /send_to_home is up and running!')

    def handle_send_to_home(self, _request, response):
        self.get_logger().info('Received SendToHome request, teleporting turtle...')

        if not self.teleport_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().warn('/turtle1/teleport_absolute not available')
            response.success = False
            response.message = 'Teleport service not available'
            return response

        teleport_req = TeleportAbsolute.Request()
        teleport_req.x = INITIAL_X
        teleport_req.y = INITIAL_Y
        teleport_req.theta = INITIAL_THETA
        self.teleport_client.call_async(teleport_req)

        response.success = True
        response.message = f'Turtle teleported to initial position: x={INITIAL_X:.2f}, y={INITIAL_Y:.2f}'
        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = TurtleControlServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
