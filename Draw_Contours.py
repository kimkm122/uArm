import os
import sys
import time
import cv2
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from uarm.wrapper import SwiftAPI

#Initialize Swift Parameters
swift = SwiftAPI(filters={'hwid': 'USB VID:PID=2341:0042'})
swift.waiting(timeout=3)
speed = 250
swift.set_mode(0)
swift.set_height_offset(offset=45)

#Swift Coordinate Constraints
x_min = 100
x_max = 500
y_min = -200
y_max = 200
z_min = 0
z_max = 100

#Load Image
source = cv2.imread('C:/Source.png', cv2.IMREAD_UNCHANGED)

#Resize Image to Scale
height, width, channels = source.shape
scale_percent = min((x_max - x_min) / height, (y_max - y_min) / width))
scale_height = int(height * scale_percent / 100)
scale_width = int(width * scale_percent / 100)
scale_dimensions = (scale_width, scale_height)
resized = cv2.resize(source, scale_dimensions)

#Extract Contours
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (3, 3), 0)
edges = cv2.Canny(blurred, 180, 200)
contours, hierarchy = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

#Draw Contours
swift.reset(wait=True, speed=speed)
for c in contours:
	swift.set_position(z=z_max)
	for i in range(len(c)):
		x, y = c[i][0]
		x_translated = int(x + x_min)
		y_translated = int(y - (scale_width / 2))
		swift.set_position(x=x_translated, y =y_translated, speed=speed)
		swift.set_position(z=z_min)
		swift.flush_cmd(wait_stop=True)
