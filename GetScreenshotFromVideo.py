import os
import sys
import cv2

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
    if len(sys.argv) < 3:
        print("ERROR: Need at least 2 additional arguments  - the first is the file that needs to be screenshotted from, the second is the time that the screenshot must be captured")
        return
    filename = os.path.basename(sys.argv[1])
    atSecond = float(sys.argv[2])

    inputDir = os.path.dirname(sys.argv[1])
    outputDir = inputDir
    if len(sys.argv) >= 4:
        outputDir = sys.argv[3]

    ScreenshotFromVideo(filename, inputDir, outputDir, atSecond)

if __name__ == "__main__":
    main()