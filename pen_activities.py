import os
import sys
import time
from math import *
import re
import glob
import cv2
import numpy as np
from uarm.wrapper import SwiftAPI

z_min = 0						#z-down position
z_max = 10						#z-up position
default_position = [100, 0, 50]	#swift reset position
default_speed = 30000			#speed when in transit (not drawing)

font_path = os.path.dirname(os.path.realpath(__file__))+'/cxf-fonts/'
font_list = [os.path.basename(x) for x in glob.glob(font_path + '*.cxf')]

#=======================================================================
class uArm:
	def __init__(self):
		#Define defaults
		self.default_x = default_position[0]
		self.default_y = default_position[1]
		self.default_z = default_position[2]
		self.default_speed = default_speed

		#Initialize Swift
		self.swift = SwiftAPI(filters={'hwid': 'USB VID:PID=2341:0042'})
		self.swift.waiting_ready(timeout=3)
		device_info = self.swift.get_device_info()
		firmware_version = device_info['firmware_version']
		if firmware_version and not firmware_version.startswith(('0.', '1.', '2.', '3.')):
			self.swift.set_speed_factor(0.0005)
		self.swift.set_mode(0)
		self.reset()

	def reset(self):
		self.swift.set_position(z=self.default_z, speed = self.default_speed)
		self.swift.flush_cmd(wait_stop = True)
		self.swift.reset(wait = True, z = self.default_z, speed = self.default_speed)
		self.swift.flush_cmd(wait_stop = True)

	def move(self, x = None, y = None, z = None, speed = None):
		self.swift.set_position(x = x, y = y , z = z, speed = speed)
		self.swift.flush_cmd(wait_stop = True)

	def finish(self):
		self.reset()
		self.swift.disconnect()

#=======================================================================
def set_pen_position():
	arm = uArm()
	arm.reset()
	confirm = input('Arm in default position.  Hit any key to continue')
	arm.move(z = z_min)
	confirm = input('Arm in drawing position.  Hit any key to continue')
	arm.finish()

#=======================================================================
class Drawing:
	def __init__(self, draw_area = [[150, 250], [-50, 50]], z_offset = 0):
		self.x_min = draw_area[0][0]
		self.x_max = draw_area[0][1]
		self.y_min = draw_area[1][0]
		self.y_max = draw_area[1][1]
		self.z_min = z_min + z_offset
		self.z_max = z_max + z_offset

	def get_edges(self, file, bilateral_kSize = 3, bilateral_sigmaColor = 75, bilateral_sigmaSpace = 75, gaussian_kSize = 9, canny_minVal = 250, canny_maxVal = 300):
		image = cv2.imread(file)
		self.image_height, self.image_width, _ = image.shape
		image = cv2.bilateralFilter(image, bilateral_kSize, bilateral_sigmaColor, bilateral_sigmaSpace)
		image = cv2.GaussianBlur(image, (gaussian_kSize, gaussian_kSize), 0)
		image = cv2.Canny(image, canny_minVal, canny_maxVal)
		return image

	def get_contours(self, image):
		#Need to rotate image 180 degrees for uArm to draw in correct orientation for some reason
		image = cv2.rotate(image, cv2.ROTATE_180)
		im2, contours, hierarchy = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
		return contours

	def get_scale(self, image):
		#height, width, channels = image.shape
		scale = min((self.x_max - self.x_min) / self.image_height, (self.y_max - self.y_min) / self.image_width)
		return scale

	def draw_contours(self, contours, image_scale = 1, contour_threshold = 5, draw_speed = 5000):
		arm = uArm()
		contour_count = len(contours)
		contour_number = 0
		for contour in contours:
			contour_number = contour_number + 1
			print(contour_number)
			speed = arm.default_speed
			arm.move(z = self.z_max, speed = speed)
			if len(contour) >= contour_threshold:
				print('drawing contour: ' + str(contour_number) + ' of ' + str(contour_count))
				for point in range(len(contour)):
					#Coordinates need to be flipped for some reason
					y, x = contour[point][0]
					y = y * image_scale
					x = x * image_scale
					x_translated = x + self.x_min
					y_translated = y - ((self.y_max - self.y_min) / 2)
					arm.move(x = x_translated, y = y_translated, speed = speed)
					arm.move(z = self.z_min, speed = arm.default_speed)
					speed = draw_speed
			else:
				print('skipping contour #: ' + str(contour_number) + ' (points = ' + str(len(contour)) + ')')
		print('done')
		arm.finish()

#=======================================================================
#This bit forked from https://github.com/LinuxCNC/simple-gcode-generators
#Modified for uArm coordinates system instead of gcode

def parse(file):
	font = {}
	key = None
	line_num = 0
	for text in file:
		line_num += 1
		end_char = re.match('^$', text) #blank line
		if end_char and key: #save the character to our dictionary
			font[key] = Character(key)
			font[key].stroke_list = stroke_list
			font[key].xmax = xmax

		new_cmd = re.match('^\[(.*)\]\s(\d+)', text)
		if new_cmd: #new character
			key = new_cmd.group(1)
			stroke_list = []
			xmax, ymax = 0, 0

		line_cmd = re.match('^L (.*)', text)
		if line_cmd:
			coords = line_cmd.group(1)
			coords = [float(n) for n in coords.split(',')]
			stroke_list += [Line(coords)]
			xmax = max(xmax, coords[0], coords[2])

		arc_cmd = re.match('^A (.*)', text)
		if arc_cmd:
			coords = arc_cmd.group(1)
			coords = [float(n) for n in coords.split(',')]
			xcenter, ycenter, radius, start_angle, end_angle = coords
			# since font defn has arcs as ccw, we need some font foo
			if ( end_angle < start_angle ):
				start_angle -= 360.0
			# approximate arc with line seg every 20 degrees
			segs = int((end_angle - start_angle) / 20) + 1
			angleincr = (end_angle - start_angle)/segs
			xstart = cos(start_angle * pi/180) * radius + xcenter
			ystart = sin(start_angle * pi/180) * radius + ycenter
			angle = start_angle
			for i in range(segs):
				angle += angleincr
				xend = cos(angle * pi/180) * radius + xcenter
				yend = sin(angle * pi/180) * radius + ycenter
				coords = [xstart,ystart,xend,yend]
				stroke_list += [Line(coords)]
				xmax = max(xmax, coords[0], coords[2])
				ymax = max(ymax, coords[1], coords[3])
				xstart = xend
				ystart = yend
	return font

def sanitize(string):
	retval = ''
	good=' ~!@#$%^&*_+=-{}[]|\:;"<>,./?'
	for char in string:
		if char.isalnum() or good.find(char) != -1:
			retval += char
		else: retval += ( ' 0x%02X ' %ord(char))
	return retval

def rotate_scale(x, y ,x_scale ,y_scale ,angle):
	Deg2Rad = 2.0 * pi / 360.0
	xx = x * x_scale
	yy = y * y_scale
	rad = sqrt(xx * xx + yy * yy)
	theta = atan2(yy,xx)
	newx=rad * cos(theta + angle*Deg2Rad)
	newy=rad * sin(theta + angle*Deg2Rad)
	return newx, newy

#=======================================================================
class Character:
	def __init__(self, key):
		self.key = key
		self.stroke_list = []

	def __repr__(self):
		return "%s" % (self.stroke_list)

	def get_xmax(self):
		try: return max([s.xmax for s in self.stroke_list[:]])
		except ValueError: return 0

	def get_ymax(self):
		try: return max([s.ymax for s in self.stroke_list[:]])
		except ValueError: return 0

#=======================================================================
class Line:
	def __init__(self, coords):
		self.xstart, self.ystart, self.xend, self.yend = coords
		self.xmax = max(self.xstart, self.xend)
		self.ymax = max(self.ystart, self.yend)

	def __repr__(self):
		return "Line([%s, %s, %s, %s])" % (self.xstart, self.ystart, self.xend, self.yend)

#=======================================================================
class Writing:
	def __init__(self, start_position = [150, 0], z_offset = 0):
		self.x_start = start_position[0]
		self.y_start = start_position[1]
		self.z_min = z_min + z_offset
		self.z_max = z_max + z_offset

	def write_text(self, string, font_file = 'normal.cxf', x_scale = 1, y_scale = 1, char_space_percent = 5, word_space_percent = 100, text_angle = 0, draw_speed = 5000):
		if font_file[-4:] != '.cxf':
			font_file += '.cxf'

		file = open(font_path + font_file, encoding = 'ISO-8859-1')
		font = parse(file)
		file.close()
		
		font_line_height = max(font[key].get_ymax() for key in font)
		font_word_space =  max(font[key].get_xmax() for key in font) * (word_space_percent/100.0)
		font_char_space = font_word_space * (char_space_percent /100.0)

		old_x = old_y = 0      # last position
		x_offset = 0           # distance along raw string in font units
		
		arm = uArm()
		for char in string:
			if char == ' ':
				x_offset += font_word_space
				continue

			print('Writing: ' + char)
			first_stroke = True
			for stroke in font[char].stroke_list:
				dx = old_x - stroke.xstart
				dy = old_y - stroke.ystart
				dist = sqrt(dx*dx + dy*dy)
				
				#Need to swap coordinates for uArm to write in correct orientation for some reason
				x1 = stroke.ystart
				y1 = -stroke.xstart - x_offset
				x1, y1 = rotate_scale(x1, y1, x_scale, y_scale, text_angle)

				if (dist > 0.001) or first_stroke:
					first_stroke = False
					arm.move(z = self.z_max, speed = arm.default_speed)
					arm.move(x = x1 + self.x_start, y = y1 + self.y_start, speed = arm.default_speed)
					arm.move(z = self.z_min, speed = arm.default_speed)

				#Coordinates swapped here again
				x2 = stroke.yend
				y2 = -stroke.xend - x_offset
				x2, y2 = rotate_scale(x2, y2, x_scale, y_scale, text_angle)

				arm.move(x = x2 + self.x_start, y = y2 + self.y_start, speed = draw_speed)

				old_x, old_y = stroke.xend, stroke.yend

			char_width = font[char].get_xmax()
			x_offset += font_char_space + char_width
		print('done')
		arm.finish()

#=======================================================================
def main():
	cmd_type = sys.argv[1]
	print('drawing')
	if cmd_type == 'draw':
		source = sys.argv[2]
		draw = Drawing()
		image = draw.get_edges(source)
		cv2.imshow('edges', image)
		print('Displaying preview')
		print('Press any key to continue, Esc to cancel')
		k = cv2.waitKey(0)
		if k == 27:
			cv2.destroyAllWindows()
			sys.exit()
		else:
			cv2.destroyAllWindows()
		scale = draw.get_scale(image)
		contours = draw.get_contours(image)
		draw.draw_contours(contours, image_scale = scale)
	elif cmd_type == 'write':
		string = sys.argv[2]
		write = Writing()
		if len(sys.argv) == 3:
			write.write_text(string)
		else:
			font_file = sys.argv[3]
			write.write_text(string, font_file = font_file)
	else:
		print('invalid command')

if __name__ == '__main__':
	main()
