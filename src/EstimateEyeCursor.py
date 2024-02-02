import json
import argparse
import pandas as pd
import cv2
import numpy as np
import os
import csv

parser = argparse.ArgumentParser()
parser.add_argument('source',help='The footage that needs to have the cursor estimated on.')
parser.add_argument('outfile',help='The output of the process of mapping.')
parser.add_argument('mapping',help='The mapping data that contains estimations of anchor positions')
parser.add_argument('events',help='The CSV file generated from the vr simulation that contains eye positions')
parser.add_argument('start',help='The start (in seconds) when the first trial actually starts',type=float)
args = parser.parse_args()

# Step 1: Read the mapping data
with open(args.mapping) as jsonfile:
    mapping = json.load(jsonfile)

# Step 2: Get the transformation matrix from the mapping data. Define the transformation defintion
transformation_matrix = np.array(mapping['transformation_matrix'])
def transform(input):
    A = np.array(input + [1])
    return np.dot(A,transformation_matrix)

# Read the events data
events_df = pd.read_csv(args.events)
events_start = events_df.iloc[0]['unix_ms']
eye_df = events_df[
    (events_df['event_type'] == 'Eye Tracking') 
    & (events_df['description'] == 'Screen Position')
    & (events_df['title'] == 'Left')
]
eye_df['unix_rel'] = eye_df['unix_ms'].apply(lambda x: (x-events_start)/1000.0)
print(eye_df.head(20))
print(eye_df.tail(20))

cap = cv2.VideoCapture(args.source)
capw  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))   # float `width`
caph = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))   # float `height`
capfps = int(cap.get(cv2.CAP_PROP_FPS))          # FPS
print(capw, caph, capfps)
out = cv2.VideoWriter(args.outfile, cv2.VideoWriter_fourcc('M','J','P','G'), capfps, (capw,caph))

fields = ['unix_ts', 'frame', 'x', 'y']
csv_outdir = os.path.dirname(args.outfile)
csv_outname = os.path.splitext(os.path.basename(args.outfile))[0]
csv_outfile = os.path.join(csv_outdir, f'{csv_outname}.csv')

with open(csv_outfile, 'w') as csvfile:
    # creating a csv writer object
    csvwriter = csv.writer(csvfile) 
    # writing the fields
    csvwriter.writerow(fields) 

    prev_timestamp = 0.0
    frame_counter = 0
    eye_pos = None
    while(cap.isOpened()):
        success, frame = cap.read()
        if success:
            frame_counter += 1
            ts = (cap.get(cv2.CAP_PROP_POS_MSEC) / 1000) - args.start
            result = np.copy(frame)
            #result = cv2.drawMarker(result, [int(img_center[0]),int(img_center[1])], (0,255,255), cv2.MARKER_CROSS, 20, 2)
            # print("for frame : " + str(frame_no) + "   timestamp is: ", str(cap.get(cv2.CAP_PROP_POS_MSEC)))
            eye_positions = eye_df[(eye_df['unix_rel'] >= prev_timestamp) & (eye_df['unix_rel'] < ts)]
            if not eye_positions.empty:
                ep = eye_positions.loc[eye_positions.index[0]]
                eye_pos_est = transform([ep['x'], ep['y']])
                eye_pos = (int(eye_pos_est[0]), int(caph-eye_pos_est[1]))
                # we only update the csv if the eye position is new
                csvwriter.writerow([ts, frame_counter, eye_pos[0], eye_pos[1]])
            if eye_pos is not None:
                result = cv2.drawMarker(result, eye_pos, (255,0,0), cv2.MARKER_CROSS, 20, 2)
            out.write(result)
            prev_timestamp = ts
        else:
            break

cap.release()
out.release()