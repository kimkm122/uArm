import cv2
import numpy as np

def test_smoothing(file):
	#Load Image
	image = cv2.imread(file)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	
	#Test Bilateral Filter
	bilateralArg1 = [3, 9, 15]
	bilateralArg2 = [25, 75, 125]
	for arg1 in bilateralArg1:
		for arg2 in bilateralArg2:
			output = cv2.bilateralFilter(gray, arg1, arg2, arg2)
			filename = 'bilateralFilter_' + str(arg1) + '_' + str(arg2) + '.png'
			cv2.imwrite(filename, output)

	#Test GaussianBlur
	gaussianArg = [3, 5, 7, 9]
	for arg in gaussianArg:
		output = cv2.GaussianBlur(gray, (arg, arg), 0)
		filename = 'gaussianBlur_' + str(arg) + '.png'
		cv2.imwrite(filename, output)

	#Test MedianBlur
	medianArg = [3, 5, 7, 9]
	for arg in medianArg:
		output = cv2.medianBlur(gray, arg)
		filename = 'medianBlur_' + str(arg) + '.png'
		cv2.imwrite(filename, output)
	
	#Test Canny Edges
	edgesArg = [[100, 200], [100, 300], [200, 300], [200, 400], [300, 400]]
	for arg in edgesArg:
		output = cv2.Canny(gray, arg[0], arg[1])
		filename = 'cannyEdges_' + str(arg[0]) + '_' + str(arg[1]) + '.png'
		cv2.imwrite(filename, output)

def main():
	arg_file = sys.argv[1]
	test_smoothing(arg_file)
	
if __name__ == '__main__':
	main()
