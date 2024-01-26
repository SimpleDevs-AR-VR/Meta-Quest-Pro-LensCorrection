import os
import sys
import cv2

def ScreenshotFromVideo(videoFilename, inputDir, outputDir, atSecond=0.0):
    filename, file_extension = os.path.splitext(videoFilename)
    # Read the video from specified path
    videoCaptureName = os.path.join(inputDir, videoFilename)
    print(f"Attempting to read capture from: {videoCaptureName}")
    cam = cv2.VideoCapture(videoCaptureName)
    # just cue to 20 sec. position
    cam.set(cv2.CAP_PROP_POS_MSEC,atSecond*1000)
    success,image = cam.read()
    imageFilename = filename + ".png"
    if success:
        print("Screenshot successfully extracted.")
        newFilename = os.path.join(outputDir, imageFilename)
        print(f"Saving file as: {newFilename}")
        cv2.imwrite(newFilename, image)     # save frame as JPEG file
    else:
        print("Unable to extract screenshot...")
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

    print(f"Saving file to: {outputDir}")
    ScreenshotFromVideo(filename, inputDir, outputDir, atSecond)

if __name__ == "__main__":
    main()