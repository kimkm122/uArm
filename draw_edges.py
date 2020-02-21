import os
import sys
import time
import cv2
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from uarm.wrapper import SwiftAPI

#Global Swift Parameters
x_min = 150
x_max = 250
y_min = -50
y_max = 50
z_min = 0
z_max = 30
speed = 10000

def get_contours(file):
	#Load Image
	image = cv2.imread(file)
	
	#Resize Image to Scale
	height, width, channels = image.shape
	scale_percent = min((x_max - x_min) / height, (y_max - y_min) / width)
	scale_height = int(height * scale_percent)
	scale_width = int(width * scale_percent)
	scale_dimensions = (scale_width, scale_height)
	resized = cv2.resize(image, scale_dimensions)
	
	#Extract Contours
	gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
	smoothed = cv2.bilateralFilter(gray, 9, 75, 75)
	blurred = cv2.GaussianBlur(smoothed, (3, 3), 0)
	edges = cv2.Canny(blurred, 300, 350)
	im2, contours, hierarchy = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
	return contours

def draw_contours(contours):
	#Initialize Swift
	swift = SwiftAPI(filters={'hwid': 'USB VID:PID=2341:0042'})
	swift.waiting_ready(timeout=3)
	device_info = swift.get_device_info()
	print(device_info)
	firmware_version = device_info['firmware_version']
	if firmware_version and not firmware_version.startswith(('0.', '1.', '2.', '3.')):
		swift.set_speed_factor(0.0005)
	swift.set_mode(0)
	
	#Draw Contours
	print('reseting position')
	swift.reset(wait=True, z=z_max, speed=speed)
	contour_count = len(contours)
	for c in contours:
		contour_num = contour_num + 1
		print('drawing contour ' + str(contour_num) + ' of ' + str(contour_count))
		swift.set_position(z=z_max)
		swift.flush_cmd(wait_stop=True)
		for i in range(len(c)):
			x, y = c[i][0]
			x_translated = int(x + x_min)
			y_translated = int(y - ((y_max - y_min) / 2))
			#swift.set_position(x=x_translated, y =y_translated, speed=speed)
			#swift.set_position(z=z_min)
			#swift.flush_cmd(wait_stop=True)
	
	swift.reset(wait=True, z=z_max, speed=speed)
	swift.flush_cmd()
	time.sleep(1)
	swift.disconnect()

def main():
	arg_file = sys.argv[1]
	contours = get_contours(arg_file)
	draw_contours(contours)
	
if __name__ == '__main__':
	main()
