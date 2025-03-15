import numpy as np
import os
import cv2 as cv
import easyocr
import argparse
from GetScreenshotFromVideo import ScreenshotFromVideo

reader = easyocr.Reader(['en'])

parser = argparse.ArgumentParser()
parser.add_argument('source',help='The footage that we want to sample from')
parser.add_argument('timestamp',
                    help='The timestamp (in sec) we want to sample',
                    type=float)
parser.add_argument('-thr', '--threshold',
                    help='The threshold value for OCR',
                    type=int,
                    default=100)
args = parser.parse_args()

_dir = os.path.dirname(args.source)
_basename = os.path.basename(args.source)
_filename = os.path.splitext(_basename)[0]

print(_dir, _basename, _filename)

# Get screenshot at the selected second
_outfile = ScreenshotFromVideo(_basename, _dir, _dir, args.timestamp)
# Load image
img = cv.imread(os.path.join(_dir,_outfile))

# Grayscale
gry = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
gry_filename = os.path.join(_dir, _basename+'_gray.jpg')

thr = cv.threshold(gry, args.threshold, 255, cv.THRESH_BINARY)[1]
thr_filename = os.path.join(_dir, _basename+'_thr.jpg')

screen_text = reader.readtext(thr)
if len(screen_text) > 0:
    print(screen_text)

cv.imwrite(gry_filename, gry)
cv.imwrite(thr_filename, thr)

