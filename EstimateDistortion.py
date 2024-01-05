# Python program to illustrate HoughLine
# method for line detection
import cv2
import numpy as np
import os
import time
import subprocess

_INPUT_DIR = "inputs/"
_MID_DIR = "processing/"
_OUTPUT_DIR = "outputs/"

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