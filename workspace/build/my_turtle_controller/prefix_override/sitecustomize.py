import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/ars/ros2-labs-sem8/workspace/install/my_turtle_controller'
