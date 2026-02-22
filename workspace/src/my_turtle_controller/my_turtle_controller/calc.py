import math
from math import pi

linear_speed = 2.0 #m/s
angular_speed = 2.0 #rad/s
smaller_angle_deg = 30 #can be changed!!!
smaller_angle = math.radians(smaller_angle_deg)
print(smaller_angle)
bigger_angle = math.radians(180-90-smaller_angle_deg)
print(bigger_angle)     
first_leg_time = 2 #can be changed. affects hypot and second leg length
smaller_angle_time = smaller_angle/angular_speed
hypot_time = ((first_leg_time * linear_speed) / math.cos(smaller_angle)) / linear_speed
bigger_leg_time = ((first_leg_time * linear_speed) * math.tan(smaller_angle)) / linear_speed
bigger_angle_time = bigger_angle/angular_speed
reset_angle_time = (2*pi - bigger_angle - smaller_angle)/angular_speed