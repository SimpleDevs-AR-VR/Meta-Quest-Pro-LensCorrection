import numpy as np
import pandas as pd
import FindTemplateFromImage as FT
import cv2
import math 
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('capture',help="The relative path to the raw SCRCPY capture")
parser.add_argument('events',help='The relative path to the CVS file that captured events in the VR simulation')
parser.add_argument('outfile',help='The JSON file where to output the results')
args = parser.parse_args()

# raw data
_TEMPLATES = {
    'center':'./template/Center.png',
    'topleft':'./template/TopLeft.png',
    'topright':'./template/TopRight.png',
    'bottomleft':'./template/BottomLeft.png'
}
_REF_FRAME = cv2.imread(args.capture)
_REF_HEIGHT, _REF_WIDTH, _ = _REF_FRAME.shape
print(_REF_HEIGHT, _REF_WIDTH)
_EVENTS_DF = pd.read_csv(args.events)

# Step 1: Parse the events data from the VR simulation, get the equivalent in WorldToScreenPoint coords
cam_rows = _EVENTS_DF[
    (_EVENTS_DF['event_type'] == "Anchor") 
    & (_EVENTS_DF['title'] == "Left")
]
cam_center = cam_rows[cam_rows['description'] == "Center"].values[0]
cam_topleft = cam_rows[cam_rows['description'] == "Top Left"].values[0]
cam_topright = cam_rows[cam_rows['description'] == "Top Right"].values[0]
cam_bottomleft = cam_rows[cam_rows['description'] == "Bottom Left"].values[0]
print(cam_center)
# Note that the origin is on the bottom left
_VR_ANCHOR_POSITIONS = {
    'center':{'x':cam_center[4],'y':cam_center[5],'coords':[cam_center[4],cam_center[5]]},
    'topleft':{'x':cam_topleft[4],'y':cam_topleft[5],'coords':[cam_topleft[4],cam_topleft[5]]},
    'topright':{'x':cam_topright[4],'y':cam_topright[5],'coords':[cam_topright[4],cam_topright[5]]},
    'bottomleft':{'x':cam_bottomleft[4],'y':cam_bottomleft[5],'coords':[cam_bottomleft[4],cam_bottomleft[5]]}
}

# Step 2: calculate the image positions of each template
_IMAGE_ANCHOR_POSITIONS = {}
for key, value in _TEMPLATES.items():
    mean_center, median_center = FT.FindTemplateMatch(_REF_FRAME, value, thresh=0.975)
    # Note that the coordinates are provided in (x,y) format, with respect to the origin being on the topleft corner
    # We need to remap these coordinates to be relative to the bottom left instead
    new_y = _REF_HEIGHT - median_center[1]
    _IMAGE_ANCHOR_POSITIONS[key] = {
        'x':median_center[0],
        'y':new_y,
        'coords':[median_center[0],new_y]
    }

# INTERMISSION: Print out current results
print("FROM VR:", _VR_ANCHOR_POSITIONS)
print("FROM CV2:", _IMAGE_ANCHOR_POSITIONS)

# Step 3: Swet up system of equations
vr_coords = np.array([
    _VR_ANCHOR_POSITIONS['center']['coords'],
    _VR_ANCHOR_POSITIONS['topleft']['coords'],
    _VR_ANCHOR_POSITIONS['topright']['coords'],
    _VR_ANCHOR_POSITIONS['bottomleft']['coords']
])
img_coords = np.array([
    _IMAGE_ANCHOR_POSITIONS['center']['coords'],
    _IMAGE_ANCHOR_POSITIONS['topleft']['coords'],
    _IMAGE_ANCHOR_POSITIONS['topright']['coords'],
    _IMAGE_ANCHOR_POSITIONS['bottomleft']['coords']
])
# Square matrix
A = np.vstack([vr_coords.T, np.ones(4)]).T
print(A)
# Least squares method
x, res, rank, s = np.linalg.lstsq(A, img_coords, rcond=None)
print(x)

# Now, we can calculate the estimated transformation from vr to img coordinates using np.dot
# In other words, `x` is the transformation matrix. It will be a 3x2 matrix
# All that needs to be done beforehand is to create `A`.
# The transformation results in Ax => (nx3)(3x2) where `n` is the number of coordinates you want to transform
print(np.dot(A,x))

"""
# Step 3: Calculate width and height of the original VR and of the CV2
# Remember that all coordinates are in (y,x).
# To get width, find difference between values of index 1
# to get height, find difference between values of index 0
_VR_WIDTH = math.dist(_VR_ANCHOR_POSITIONS['topright']['coords'], _VR_ANCHOR_POSITIONS['topleft']['coords'])
_VR_HEIGHT = math.dist(_VR_ANCHOR_POSITIONS['bottomleft']['coords'], _VR_ANCHOR_POSITIONS['topleft']['coords'])
_IMG_WIDTH = math.dist(_IMAGE_ANCHOR_POSITIONS['topright']['coords'], _IMAGE_ANCHOR_POSITIONS['topleft']['coords'])
_IMG_HEIGHT = math.dist(_IMAGE_ANCHOR_POSITIONS['bottomleft']['coords'], _IMAGE_ANCHOR_POSITIONS['topleft']['coords'])
print(f"VR WIDTH AND HEIGHT: w={_VR_WIDTH} ; h={_VR_HEIGHT}")
print(f"IMG WIDTH AND HEIGHT: w={_IMG_WIDTH} ; h={_IMG_HEIGHT}")

# Step 4: Calcualte the halves of these
_VR_WIDTH_HALF = _VR_WIDTH / 2.0
_VR_HEIGHT_HALF = _VR_HEIGHT / 2.0
_IMG_WIDTH_HALF = _IMG_WIDTH / 2.0
_IMG_HEIGHT_HALF = _IMG_HEIGHT / 2.0

# Step 5: Save Results
output = {
    'vr_anchors_positions':_VR_ANCHOR_POSITIONS,
    'img_anchors_positions':_IMAGE_ANCHOR_POSITIONS,
    'vr':{
        'width':_VR_WIDTH,
        'height':_VR_HEIGHT,
        'width_half':_VR_WIDTH_HALF,
        'height_half':_VR_HEIGHT_HALF
    },
    'img':{
        'width':_IMG_WIDTH,
        'height':_IMG_HEIGHT,
        'width_half':_IMG_WIDTH_HALF,
        'height_half':_IMG_HEIGHT_HALF
    }
}
"""
output = {
    'vr_anchors_positions':_VR_ANCHOR_POSITIONS,
    'img_anchors_positions':_IMAGE_ANCHOR_POSITIONS,
    'transformation_matrix':x.tolist()
}
with open(args.outfile, "w") as outfile: 
    json.dump(output, outfile, indent=4)

"""
Why we need to do this:
We need a method to transform eye capture position footage, captured on the Meta Quest Pro, into points on the actual image.
We can't do this normally because there's no way to keep the footage from the eye and the footage from the SCRCPY separate.
In other words, we can't have two streams occurring at once. This means we can't have clean footage without the eye cursor, then overlay the eye cursor on top; they HAVE to be combined together.
So the alternative instead is to do something crazy: we instead capture the WorldToScreen position of the eye cursor, then translate that into the lens-corrected output using OpenCV
This way, we can have the separate, clean footage for tasks such as YOLO object detection and then overlap the eye cursor on top after doing so.

The formula for this requires that we understand the width and height of the WorldToScreen equivalent of the scene, all managed by Unity
The formula is such that:
1. Calculate the relational ratio of the eye cursor's screen position to the screen position of the center
    ((cursor.screenpoint - screencenter) / (vr_height_half, vr_width_half))
2. With the ratio, we can then remap to the lens-corrected position
    (cursor.ratio * (img_height_half, img_width_half)) + correctedcenter

(noting that positions are in (y,x) format due to OpenCV)
"""

world = np.array([
    [0,0,0],
    [7,0,0],
    [0,5,0],
    [7,4,0]])
    
camera = np.array([
    [582,344],
    [834,338],
    [586,529],
    [841,522]])
    
#Lose Z axis
world = world[:,0:2]

#Make a square matrix
A = np.vstack([world.T, np.ones(4)]).T

#perform the least squares method
x, res, rank, s = np.linalg.lstsq(A, camera, rcond=None)

#test results
print(np.dot(A,x))