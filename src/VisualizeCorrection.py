import numpy as np
import os
import cv2
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('source',help="The source image to visualize")
args = parser.parse_args()

src_img = cv2.imread(args.source)
basename = os.path.basename(args.source)
filename = os.path.splitext(basename)[0]

output_img = np.copy(src_img)
output_filename = f'{filename}_temp.png'
cx = 50
cy = 50
k2 = 50
k1 = 50
def nothing(x):
    global output_img, cx, cy, k2, k1, output_filename
    _cx = threshold_value = cv2.getTrackbarPos('cx', window_name)
    _cy = threshold_value = cv2.getTrackbarPos('cy', window_name)
    _k2 = threshold_value = cv2.getTrackbarPos('k2', window_name)
    _k1 = threshold_value = cv2.getTrackbarPos('k1', window_name)
    cx = float(_cx/100.0)
    cy = float(_cy/100.0)
    k2 = float((_k2-50.0)/50.0)
    k1 = float((_k1-50.0)/50.0)
    cmd_str = 'ffmpeg -y -i {} -vf "lenscorrection=cx={}:cy={}:k2={}:k1={}" -vsync 2 {}'.format(
            args.source, cx, cy, k2, k1, output_filename)
    correction_code = os.system(cmd_str)
    if correction_code == 0:
        output_img = cv2.imread(output_filename) 

window_name = f"Lens correction: {basename}"
cv2.namedWindow(window_name)
cv2.createTrackbar('cx', window_name, 50, 100, nothing)
cv2.createTrackbar('cy', window_name, 50, 100, nothing)
cv2.createTrackbar('k2', window_name, 50, 100, nothing)
cv2.createTrackbar('k1', window_name, 50, 100, nothing)

while True:
    frame = cv2.imread(output_filename)
    fshape = np.shape(frame)
    p = [int(cx*fshape[0]),int(cy*fshape[1])]
    out_frame = cv2.drawMarker(frame,p,[0,255,255],cv2.MARKER_CROSS,5,3)
    cv2.imshow(window_name, out_frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
