#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

#клиент для action-сервера draw_figure. управление по положению из лаб 3, траектория из лаб 1

from my_turtle_interface.action import DrawFigure


class TurtleActionClient(Node):
    def __init__(self):
        super().__init__('turtle_action_client')
        self._action_client = ActionClient(self, DrawFigure, 'draw_figure')
        self.get_logger().info('Waiting for action server...')
        self._action_client.wait_for_server()
        self.get_logger().info('Server found, sending goal...')
        self.send_goal()

    def send_goal(self):
        goal_msg = DrawFigure.Goal()
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected!')
            return
        self.get_logger().info('Goal accepted!')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().info(f'FEEDBACK: vertex {fb.vertex_reached} - {fb.status}')

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'MISSION RESULT: success={result.success}, {result.message}')


def main(args=None):
    rclpy.init(args=args)
    node = TurtleActionClient()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
