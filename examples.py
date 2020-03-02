import pen_activities as pen
import cv2

pen.set_pen_position()
#Draw outline
#draw = pen.Drawing(draw_area = [[150, 250], [-50, 50]])
#draw.draw_border()

#Example Drawing
#draw = pen.Drawing(draw_area = [[150, 250], [-50, 50]])
#image = draw.get_edges('samples/cat.png')
#scale = draw.get_scale(image)
#contours = draw.get_contours(image)
#draw.draw_contours(contours, image_scale = scale)

#draw = draw = pen.Drawing(draw_area = [[150, 250], [-50, 50]])
#image = draw.get_edges('samples/cat.png')
#scale = draw.get_scale(image)
#contours = draw.get_contours(image)
#draw.draw_contour_stipples(contours, image_scale = scale)

#Example Stipple
draw = pen.Drawing(draw_area = [[150, 250], [50, 150]])
stipples = draw.get_numpy_stipples('samples/20000.npy')
draw.draw_stipples(stipples)

#Example Writing
#write = pen.Writing(start_position = [255, 0])
#write.write_text('Momo', font_file = 'gothgbt.cxf')
