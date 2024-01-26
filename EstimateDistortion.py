# Python program to illustrate HoughLine
# method for line detection
import cv2
import numpy as np
import os
import time
import subprocess
import argparse
from glob import glob

parser = argparse.ArgumentParser()
parser.add_argument('source', help="The source (image or video) that is used as the template to run the lens correction on.")
parser.add_argument('template', help="The template file (image) that will be used as a reference for the number of lines that ought to be detected.")
args = parser.parse_args()

input_basename = os.path.basename(args.source)
input_filename = os.path.splitext(input_basename)[0]

# We have to check for any runs on this
_OUTPUT_ROOT = "estimate_distortion_runs/"
_OUTPUT_DIR = os.path.join(_OUTPUT_ROOT, input_filename)
output_counter = 1
while os.path.exists(_OUTPUT_DIR):
    _OUTPUT_DIR = os.path.join(_OUTPUT_ROOT, f'{input_filename}_{output_counter}')
    output_counter+=1
os.makedirs(_OUTPUT_DIR)
print(f"OUTPUT DIRECTORY: {_OUTPUT_DIR}")

# We need to somehow determine the focal center of the image.
# We'll do this by clicking on the approximate focal point
# First, load in the image
src = cv2.imread(args.source)
# Next, let's define a global function that we'll pass the click values into
focal_center = None
# Next, let's define a mouseclick function to help us with this endeavor
def mouseRGB(event,x,y,flags,param):
    global focal_center
    if event == cv2.EVENT_LBUTTONDOWN: #checks mouse left button down condition
        colorsB = src[y,x,0]
        colorsG = src[y,x,1]
        colorsR = src[y,x,2]
        colors = src[y,x]
        print("Red: ",colorsR)
        print("Green: ",colorsG)
        print("Blue: ",colorsB)
        print("BRG Format: ",colors)
        print("Coordinates of pixel: X: ",x,"Y: ",y)
        focal_center = [y,x] # in Y, X format

# Next, attach the mouse events
focal_point_window = 'Focal Point Color Selector'
cv2.namedWindow(focal_point_window)
cv2.setMouseCallback(focal_point_window, mouseRGB)
# Next, run the while loop until we select the image with a confirmation
while True:
    cv2.imshow(focal_point_window, src)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
if focal_center is None:
    print("EXITING EARLY FROM APPLICATION DUE TO LACK OF FOCAL POINT BGR")
    exit(1)

# If we got this far, we know the focal x and y from `focal_center`
# We now have to derive the percentage between 0 and 1 for `cx` and `cy`
src_shape = np.shape(src)
cy = float(focal_center[0] / src_shape[0])
cx = float(focal_center[1] / src_shape[1])
print(f"FOCAL CENTER [by percentage]: cx={cx}, cy={cy}")

# NOW is the big kahuna - we need to estimate all the possible parameters for k2 and k1

# First, let's start by defining some folders
# Determine our processing, and results directories
_CORRECTIONS_DIR = os.path.join(_OUTPUT_DIR, "processing/")
_RESULTS_DIR = os.path.join(_OUTPUT_DIR, "results/")
os.makedirs(_CORRECTIONS_DIR)
os.makedirs(_RESULTS_DIR)

# Next, let's define a helper function
# This function simply adds Hough Lines after applying the Canny filter
# This is effectively a way to determine the edges of the image (edge detection via canny)...
# ... then do line detection via Hough lines
def GetLinesFromImage(imageFilename, resultsFilename=None):
    img = cv2.imread(imageFilename)
    # Convert the img to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Apply edge detection method on the image
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    # This returns an array of r and theta values
    lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
  
    # The below for loop runs till r and theta values
    # are in the range of the 2d array
    for r_theta in lines:
        arr = np.array(r_theta[0], dtype=np.float64)
        r, theta = arr
        # Stores the value of cos(theta) in a
        a = np.cos(theta)
        # Stores the value of sin(theta) in b
        b = np.sin(theta)
        # x0 stores the value rcos(theta)
        x0 = a*r
        # y0 stores the value rsin(theta)
        y0 = b*r
        # x1 stores the rounded off value of (rcos(theta)-1000sin(theta))
        x1 = int(x0 + 1000*(-b))
        # y1 stores the rounded off value of (rsin(theta)+1000cos(theta))
        y1 = int(y0 + 1000*(a))
        # x2 stores the rounded off value of (rcos(theta)+1000sin(theta))
        x2 = int(x0 - 1000*(-b))
        # y2 stores the rounded off value of (rsin(theta)-1000cos(theta))
        y2 = int(y0 - 1000*(a))
        # cv2.line draws a line in img from the point(x1,y1) to (x2,y2).
        # (0,0,255) denotes the colour of the line to be
        # drawn. In this case, it is red.
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
    
    print("Number of lines: {}".format(len(lines)))
    # All the changes made in the input image are finally
    # written on a new image houghlines.jpg
    if resultsFilename is not None:
        cv2.imwrite(resultsFilename, img)
    return lines, img

# With the function defined, we can now begin to loop through all possible values of k2 and k1
# Note that k1 and k2 can be any value between -1 and 1... so this will take a while

# For starters, let's attempt to see how many hough lines are detected in the original file we ought to be referencing
template_output_filename = os.path.join(_OUTPUT_DIR, "template_lines.png")
template_lines, template_result = GetLinesFromImage(args.template, template_output_filename)
n_template = len(template_lines)
print(f"Detected {n_template} in the template")

# We'll store the results in an array for now
results = []
for k1 in np.arange(-1.0,1.0,0.01):
    for k2 in np.arange(-1.0,1.0,0.01):
        _k1 = round(k1,2)
        _k2 = round(k2,2)
        print("Testing: k1={}, k2={}".format(_k1, _k2))
        corrected_filepath = f"{_CORRECTIONS_DIR}temp.png"
        cmd_str = 'ffmpeg -y -i {} -vf "lenscorrection=cx={}:cy={}:k2={}:k1={}" -vsync 2 {}'.format(
            args.source, cx, cy, _k2, _k1, corrected_filepath)
        print("\tCommand:",cmd_str)

        # Check if successful
        correction_code = os.system(cmd_str)
        if correction_code == 0:
            # We were successful, so we can continue parsing the image
            print("\tCorrection applied, Checking for Lines")
            # Process the image

            output_filename = "{}{}_{}.png".format(_RESULTS_DIR,_k2,_k1)
            output_lines, output_img = GetLinesFromImage(corrected_filepath)
            results.append([len(output_lines), output_filename, output_img])
            os.remove(corrected_filepath)

# Finally... let's check which images are similar to our template in terms of line number
# We'll do this by sorting 
results.sort( key = lambda x: abs(x[0]-n_template))
# We'll cutoff by the top 10
results_100 = results[:100]
# Save the results of each
for res in results_100:
    cv2.imwrite(res[1], res[2])

"""
_SAMPLE_IMAGE = "Sample.png"                                        # must be placed inside of `_INPUT_DIR`
_SOURCE_VIDEO = "DistortionTest_3648_1920_0_0_1824_NoDisplay.mp4"   # Must be placed inside of `_INPUT_DIR`

_CROP_PARAMS = [912,960,12.5,0]
_FOCAL_CENTER = [0.55, 0.43]
_TIME_AT_IMAGE_PARSE = 11.0

def GetLinesFromImage(imageFilename, inputDir, outputDir):
    filename, file_extension = os.path.splitext(imageFilename)
    img = cv2.imread(inputDir+imageFilename)
    # Convert the img to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply edge detection method on the image
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
  
    # This returns an array of r and theta values
    lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
  
    # The below for loop runs till r and theta values
    # are in the range of the 2d array
    for r_theta in lines:
        arr = np.array(r_theta[0], dtype=np.float64)
        r, theta = arr
        # Stores the value of cos(theta) in a
        a = np.cos(theta)
    
        # Stores the value of sin(theta) in b
        b = np.sin(theta)
    
        # x0 stores the value rcos(theta)
        x0 = a*r
    
        # y0 stores the value rsin(theta)
        y0 = b*r
    
        # x1 stores the rounded off value of (rcos(theta)-1000sin(theta))
        x1 = int(x0 + 1000*(-b))
    
        # y1 stores the rounded off value of (rsin(theta)+1000cos(theta))
        y1 = int(y0 + 1000*(a))
    
        # x2 stores the rounded off value of (rcos(theta)+1000sin(theta))
        x2 = int(x0 - 1000*(-b))
    
        # y2 stores the rounded off value of (rsin(theta)-1000cos(theta))
        y2 = int(y0 - 1000*(a))
    
        # cv2.line draws a line in img from the point(x1,y1) to (x2,y2).
        # (0,0,255) denotes the colour of the line to be
        # drawn. In this case, it is red.
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
    
    print("Number of lines: {}".format(len(lines)))
    
    # All the changes made in the input image are finally
    # written on a new image houghlines.jpg
    cv2.imwrite(outputDir + filename + '-lines.png', img)

def ScreenshotFromVideo(videoFilename, inputDir, outputDir, atSecond=0.0):
    filename, file_extension = os.path.splitext(videoFilename)
    # Read the video from specified path
    cam = cv2.VideoCapture(inputDir + videoFilename)
    # just cue to 20 sec. position
    cam.set(cv2.CAP_PROP_POS_MSEC,atSecond*1000)
    success,image = cam.read()
    imageFilename = filename + ".png"
    if success:
        cv2.imwrite(outputDir + imageFilename, image)     # save frame as JPEG file
    else:
        imageFilename = None
    cam.release()
    return imageFilename

def main():
    # Get the main from sample
    GetLinesFromImage(_SAMPLE_IMAGE, _INPUT_DIR, _OUTPUT_DIR)

    # Now that we have a source, we can generate new distortions and test them if they match the sample
    # k1 range: -0.6 to -0.5, increments of 0.01
    # k2 range: 0.2 to 0.3, increments of 0.01
    test_video = _INPUT_DIR + _SOURCE_VIDEO

    for k1 in np.arange(-0.7,-0.29,0.01):
        for k2 in np.arange(0.0,0.41,0.01):
            _k1 = round(k1,2)
            _k2 = round(k2,2)
            print("Testing: k1={}, k2={}".format(_k1, _k2))

            corrected_video_path = "{}_{}.mp4".format(_k2,_k1)

            cmd_str = 'ffmpeg -y -i {} -vf "crop={}:{}:{}:{},lenscorrection=cx={}:cy={}:k2={}:k1={}" -vsync 2 {}{}'.format(
                test_video,
                _CROP_PARAMS[0], _CROP_PARAMS[1], _CROP_PARAMS[2], _CROP_PARAMS[3],
                _FOCAL_CENTER[0], _FOCAL_CENTER[1],
                _k2,_k1,
                _MID_DIR,
               corrected_video_path
            )
            print("\tCommand:",cmd_str)

            # Check if successful
            correction_code = os.system(cmd_str)
            if correction_code == 0:
                # We were successful, so we can continue parsing the image
                print("\tCorrection applied, Checking for Lines")
                corrected_image = ScreenshotFromVideo(corrected_video_path, _MID_DIR, _MID_DIR, _TIME_AT_IMAGE_PARSE)
                # Process the image
                GetLinesFromImage(corrected_image, _MID_DIR, _OUTPUT_DIR)


    #videoFile = "distorted.mp4"
    #generatedImageFilename = ScreenshotFromVideo(videoFile, 5.0)
    #GetLinesFromImage(generatedImageFilename)
    #filename = "images/testcorrection"
    #GetLinesFromImage(filename)

if __name__ == "__main__":
    main()
"""