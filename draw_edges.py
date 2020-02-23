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
z_max = 10
speed_move = 30000
speed_draw = 5000
scale_percent = 0.25
contour_thresh = 5

def get_contours(file):
	#Load Image
	image = cv2.imread(file)

	#Resize Image to Scale
	global scale_percent
	height, width, channels = image.shape
	scale_percent = min((x_max - x_min) / height, (y_max - y_min) / width)

	#Extract Contours
	imgage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	image = cv2.bilateralFilter(image, 3, 75, 75)
	image = cv2.GaussianBlur(image, (9, 9), 0)
	edges = cv2.Canny(image, 250, 300)
	cv2.imshow('egdges', edges)
	print('Displaying preview')
	print('Press any key to continue, Esc to cancel')
	k = cv2.waitKey(0)
	if k == 27:
		cv2.destroyAllWindows()
		sys.exit()
	else:
		cv2.destroyAllWindows()
	edges = cv2.rotate(edges, cv2.ROTATE_180)
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
	swift.reset(wait=True, z=50, speed=speed_move)
	contour_count = len(contours)
	contour_num = 0
	print('number of contours: ' + str(contour_count))
	try:
		for c in contours:
			contour_num = contour_num + 1
			print('drawing contour ' + str(contour_num) + ' of ' + str(contour_count))
			swift.set_position(z=z_max, speed=speed_move)
			swift.flush_cmd(wait_stop=True)
			speed = speed_move
			if len(c) >= contour_thresh:
				for i in range(len(c)):
					y, x = c[i][0]
					y =  y * scale_percent
					x =  x * scale_percent
					x_translated = x + x_min
					y_translated = y - ((y_max - y_min) / 2)
					swift.set_position(x=x_translated, y =y_translated, speed=speed)
					swift.set_position(z=z_min, speed=speed_move)
					speed = speed_draw
					swift.flush_cmd(wait_stop=True)
		print('done')
		swift.set_position(z=z_max, speed=speed_move)
		swift.reset(wait=True, z=50, speed=speed_move)
		swift.flush_cmd()
		time.sleep(1)
		swift.disconnect()
	except KeyboardInterrupt:
		sys.exit()

def main():
	start_time = time.time()
	arg_file = sys.argv[1]
	contours = get_contours(arg_file)
	draw_contours(contours)
	print('completed in %s min' % round(((time.time() - start_time))/60), 4)

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print('Interrupeted')
		sys.exit(0)
