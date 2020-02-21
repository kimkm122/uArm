import os
import sys
import time
import cv2
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from uarm.wrapper import SwiftAPI

folder = '/media/kkim/Data/Pictures/Edge_Detection'
file = 'cat02_at_iteration_5.png'
#file = 'cat02.jpeg'

#Initialize Swift Parameters
swift = SwiftAPI(filters={'hwid': 'USB VID:PID=2341:0042'})
swift.waiting_ready(timeout=3)
device_info = swift.get_device_info()
print(device_info)
firmware_version = device_info['firmware_version']
if firmware_version and not firmware_version.startswith(('0.', '1.', '2.', '3.')):
    swift.set_speed_factor(0.0005)
swift.set_mode(0)
#swift.set_height_offset(offset=45)
speed = 10000

#Swift Coordinate Constraints
x_min = 100
x_max = 300
y_min = -100
y_max = 100
z_min = 0
z_max = 30

#Load Image
#image = cv2.imread(folder + '/Source/' + file)
image = cv2.imread(file)

#Resize Image to Scale
height, width, channels = image.shape

print(height, width)
scale_percent = min((x_max - x_min) / height, (y_max - y_min) / width)
print(scale_percent)
scale_height = int(height * scale_percent)
scale_width = int(width * scale_percent)
scale_dimensions = (scale_width, scale_height)
resized = cv2.resize(image, scale_dimensions)

height, width, channels = resized.shape

print(height, width)

#Extract Contours
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (3, 3), 0)
edges = cv2.Canny(blurred, 300, 350)
_, contours, hierarchy = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

cv2.imwrite("output.png", edges)
#Draw Contours
swift.reset(wait=True, z=50, speed=speed)
print("reset")
#c = max(contours, key=cv2.contourArea)
for c in contours:
	swift.set_position(z=z_max)
	swift.flush_cmd(wait_stop=True)
	print("up")
	for i in range(len(c)):
		x, y = c[i][0]
		x_translated = int(x + x_min)
		y_translated = int(y - ((y_max - y_min) / 2))
		#swift.set_position(x=x_translated, y =y_translated, speed=speed)
		#swift.set_position(z=z_min)
		#swift.flush_cmd(wait_stop=True)
		#print(x, y)
		print(x_translated, y_translated)

swift.reset(wait=True, z=50, speed=speed)
swift.flush_cmd()
time.sleep(3)
swift.disconnect()
