from Tkinter import *
from math import *
import os
import re
import glob
from uarm.wrapper import SwiftAPI

fontPath = os.path.dirname(os.path.realpath(__file__))+'/cxf-fonts/'
fontList = [os.path.basename(x) for x in glob.glob(fontPath + '*.cxf')]
file = 'fonts/romanc.cxf'

#=======================================================================
# This routine parses the .cxf font file and builds a font dictionary of
# line segment strokes required to cut each character.
# Arcs (only used in some fonts) are converted to a number of line
# segemnts based on the angular length of the arc. Since the idea of
# this font description is to make it support independant x and y scaling,
# we can not use native arcs in the gcode.
#=======================================================================
def parse(file):
    font = {}
    key = None
    num_cmds = 0
    line_num = 0
    for text in file:
        #format for a typical letter (lowercase r):
        ##comment, with a blank line after it
        #
        #[r] 3
        #L 0,0,0,6
        #L 0,6,2,6
        #A 2,5,1,0,90
        #
        line_num += 1
        end_char = re.match('^$', text) #blank line
        if end_char and key: #save the character to our dictionary
            font[key] = Character(key)
            font[key].stroke_list = stroke_list
            font[key].xmax = xmax
            if (num_cmds != cmds_read):
                print "(warning: discrepancy in number of commands %s, line %s, %s != %s )" % (fontfile, line_num, num_cmds, cmds_read)

        new_cmd = re.match('^\[(.*)\]\s(\d+)', text)
        if new_cmd: #new character
            key = new_cmd.group(1)
            num_cmds = int(new_cmd.group(2)) #for debug
            cmds_read = 0
            stroke_list = []
            xmax, ymax = 0, 0

        line_cmd = re.match('^L (.*)', text)
        if line_cmd:
            cmds_read += 1
            coords = line_cmd.group(1)
            coords = [float(n) for n in coords.split(',')]
            stroke_list += [Line(coords)]
            xmax = max(xmax, coords[0], coords[2])

        arc_cmd = re.match('^A (.*)', text)
        if arc_cmd:
            cmds_read += 1
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
def sanitize(string):
	retval = ''
	good=' ~!@#$%^&*_+=-{}[]|\:;"<>,./?'
	for char in string:
		if char.isalnum() or good.find(char) != -1:
			retval += char
		else: retval += ( ' 0x%02X ' %ord(char))
	return retval
	
#=======================================================================
def Rotn(self,x,y,xscale,yscale,angle): 
	Deg2Rad = 2.0 * pi / 360.0 
	xx = x * xscale 
	yy = y * yscale 
	rad = sqrt(xx * xx + yy * yy) 
	theta = atan2(yy,xx) 
	newx=rad * cos(theta + angle*Deg2Rad) 
	newy=rad * sin(theta + angle*Deg2Rad) 
	return newx,newy 

#=======================================================================
def DoIt(string):
	
	z_max = 30
	z_min = 0
	XStart =   100
	YStart =   0
	XScale =   0.04
	YScale =   0.04
	CSpaceP=   25
	WSpaceP = 100
	Angle = 0
	speed = 10000
	
	oldx = oldy = 0      # last position

	font = parse(file)          # build stroke lists from font file
	file.close()

	font_line_height = max(font[key].get_ymax() for key in font)
	font_word_space =  max(font[key].get_xmax() for key in font) * (WSpaceP/100.0)
	font_char_space = font_word_space * (CSpaceP /100.0)

	xoffset = 0                 # distance along raw string in font units

	#Initialize Swift
	swift = SwiftAPI(filters={'hwid': 'USB VID:PID=2341:0042'})
	swift.waiting_ready(timeout=3)
	device_info = swift.get_device_info()
	firmware_version = device_info['firmware_version']
	if firmware_version and not firmware_version.startswith(('0.', '1.', '2.', '3.')):
		swift.set_speed_factor(0.0005)
	swift.set_mode(0)
	
	swift.reset(wait=True, z=z_max, speed=speed)
	
	for char in string:
		if char == ' ':
			xoffset += font_word_space
			continue

		first_stroke = True
		for stroke in font[char].stroke_list:
			dx = oldx - stroke.xstart
			dy = oldy - stroke.ystart
			dist = sqrt(dx*dx + dy*dy)

			x1 = stroke.xstart  + xoffset
			y1 = stroke.ystart 
			x1, y1 = Rotn(x1, y1, XScale, YScale, Angle)
			
			# check and see if we need to move to a new discontinuous start point
			if (dist > 0.001) or first_stroke:
				first_stroke = False
				#Start of new stroke
				swift.set_position(z=z_max, speed=speed)
				swift.set_position(x=x1 + XStart, y=y1 + YStart, speed=speed)
				swift.set_position(z=z_min, speed=speed)
				swift.flush_cmd(wait_stop=True)

			x2 = stroke.xend + xoffset
			y2 = stroke.yend
			x2, y2 = Rotn(x2, y2, XScale, YScale, Angle)
			
			swift.set_position(x=x2 + XStart, y=y2 + YStart, speed=speed)
			swift.flush_cmd(wait_stop=True)
			
			oldx, oldy = stroke.xend, stroke.yend

		# move over for next character
		char_width = font[char].get_xmax()
		xoffset += font_char_space + char_width

	swift.reset(wait=True, z=z_max, speed=speed)
	swift.flush_cmd(wait_stop=True)
	swift.disconnect()
