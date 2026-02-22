import math
from math import pi

linear_speed = 1.0 #m/s
angular_speed = 2.0 #rad/s
smaller_angle_deg = 30 #can be changed!!!
smaller_angle = math.radians(smaller_angle_deg)
print(smaller_angle)
smaller_angle = pi - math.radians(smaller_angle_deg)
print(smaller_angle)

bigger_angle = math.radians(180-90-smaller_angle_deg)
print(bigger_angle)

smaller_leg_time = 2 #can be changed. affects hypot and second leg length
smaller_angle_time = smaller_angle/angular_speed
smaller_leg_length = smaller_leg_time * linear_speed

hypot_time = (smaller_leg_length / math.cos(smaller_angle)) / linear_speed
print(hypot_time)


bigger_leg_time = abs(smaller_leg_length * math.tan(smaller_angle)) / linear_speed
print(bigger_leg_time)

# bigger_angle_time = bigger_angle/angular_speed
# print(bigger_angle_time)

reset_angle_time = (2*pi - bigger_angle - smaller_angle)/angular_speed