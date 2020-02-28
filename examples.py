import pen_activities as pen
import cv2

#Have a bug that prevents drawing and writing in sequence (port in use).  Only one can be run at a time.

#Example Drawing
#draw = pen.Drawing(draw_area = [[150, 250], [-50, 50]])
#image = draw.get_edges('samples/cat.png')
#scale = draw.get_scale(image)
#contours = draw.get_contours(image)
#draw.draw_contours(contours, image_scale = scale)

#Example Writing
#write = pen.Writing(start_position = [255, 0])
#write.write_text('Momo', font_file = 'gothgbt.cxf')

#Example Stipple
draw = pen.Drawing(draw_area = [[150, 250], [-50, 50]])
draw.draw_stipples('stipple.npy')
