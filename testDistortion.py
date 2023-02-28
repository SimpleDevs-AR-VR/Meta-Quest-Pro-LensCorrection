# Python program to illustrate HoughLine
# method for line detection
import cv2
import numpy as np
import os
import time
import subprocess

def GetLinesFromImage(imageFilename):
    filename, file_extension = os.path.splitext(imageFilename)
    img = cv2.imread("images/"+imageFilename)
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
    cv2.imwrite("images/" + filename + '-lines.png', img)

def ScreenshotFromVideo(videoFilename, atSecond=0.0):
    filename, file_extension = os.path.splitext(videoFilename)
    # Read the video from specified path
    cam = cv2.VideoCapture("sources/"+videoFilename)
    # just cue to 20 sec. position
    cam.set(cv2.CAP_PROP_POS_MSEC,atSecond*1000)
    success,image = cam.read()
    imageFilename = filename + ".png"
    if success:
        cv2.imwrite("images/"+imageFilename, image)     # save frame as JPEG file
    else:
        imageFilename = None
    cam.release()
    return imageFilename

def main():
    for k1 in np.arange(-0.5,-0.39,0.01):
        for k2 in np.arange(0.1,0.21,0.01):
            _k1 = round(k1,2)
            _k2 = round(k2,2)
            # For left eye
            cmd_str = 'ffmpeg -i ./sources/distorted.mp4 -vf "crop=1800:1920,lenscorrection=k1={}:k2={}" ./sources/cor_{}_{}.mp4'.format(_k1,_k2,_k1,_k2)
            result = subprocess.run(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            #print(result.stdout)
            print(result.stderr)



    #videoFile = "distorted.mp4"
    #generatedImageFilename = ScreenshotFromVideo(videoFile, 5.0)
    #GetLinesFromImage(generatedImageFilename)
    #filename = "images/testcorrection"
    #GetLinesFromImage(filename)

if __name__ == "__main__":
    main()
