import json
import argparse
import pandas as pd
import cv2
import numpy as np
import os
import csv
import matplotlib.pyplot as plt

def EstimateCursor(
        source_filepath, 
        events_filepath, 
        mapping_filepath, 
        frame_timestamps_filepath
            ):
    # Note: `sim_start_ts` is expected to be in unix seconds

    # Step 1: Read the mapping data
    with open(mapping_filepath) as jsonfile:
        mapping = json.load(jsonfile)

    # Step 2: Get the transformation matrix from the mapping data. Define the transformation defintion
    transformation_matrix = np.array(mapping['transformation_matrix'])
    def transform(input):
        A = np.array(input + [1])
        return np.dot(A,transformation_matrix)

    # Read the events data
    events_df = pd.read_csv(events_filepath)
    events_start = events_df.iloc[1]['unix_ms']
    print(events_start)
    eye_df = events_df[
        (events_df['event_type'] == 'Eye Tracking') 
        & (events_df['description'] == 'Screen Position')
        & (events_df['title'] == 'Left')
    ]
    eye_df['unix_rel'] = eye_df['unix_ms'].apply(lambda x: (x-events_start)/1000)

    # Read the frame timestamps data
    # note that all the timestamps are in seconds here. Hence the /1000 division above
    frame_ts_df = pd.read_csv(frame_timestamps_filepath)

    root_dir = os.path.dirname(source_filepath)
    out_filename = os.path.splitext(os.path.basename(source_filepath))[0]
    out_vidpath = os.path.join(root_dir, f'{out_filename}_eyecursor.avi')
    out_csvpath = os.path.join(root_dir, f'{out_filename}_eycursor.csv')

    cap = cv2.VideoCapture(source_filepath)
    capw  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))   # float `width`
    caph = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))   # float `height`
    capfps = int(cap.get(cv2.CAP_PROP_FPS))          # FPS
    out = cv2.VideoWriter(out_vidpath, cv2.VideoWriter_fourcc('M','J','P','G'), capfps, (capw,caph))

    fields = ['frame', 'x', 'y']
    with open(out_csvpath, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile) 
        # writing the fields
        csvwriter.writerow(fields) 

        prev_timestamp = 0.0
        frame_counter = -1
        eye_pos = None
        while(cap.isOpened()):
            success, frame = cap.read()
            if success:
                frame_counter += 1
                frame_row = frame_ts_df[frame_ts_df['frame'] == frame_counter].iloc[0]
                frame_ts = frame_row['timestamp']
                result = np.copy(frame)
                #result = cv2.drawMarker(result, [int(img_center[0]),int(img_center[1])], (0,255,255), cv2.MARKER_CROSS, 20, 2)
                # print("for frame : " + str(frame_no) + "   timestamp is: ", str(cap.get(cv2.CAP_PROP_POS_MSEC)))
                #print(f'{prev_timestamp} - {frame_ts}')
                eye_positions = eye_df[(eye_df['unix_rel'] >= prev_timestamp) & (eye_df['unix_rel'] < frame_ts)]
                if not eye_positions.empty:
                    ep = eye_positions.loc[eye_positions.index[0]]
                    eye_pos_est = transform([ep['x'], ep['y']])
                    eye_pos = (int(eye_pos_est[0]), int(caph-eye_pos_est[1]))
                    # we only update the csv if the eye position is new
                    csvwriter.writerow([frame_counter, eye_pos[0], eye_pos[1]])
                if eye_pos is not None:
                    result = cv2.drawMarker(result, eye_pos, (255,0,0), cv2.MARKER_CROSS, 20, 2)
                out.write(result)
                prev_timestamp = frame_ts
            else:
                break

    cap.release()
    out.release()

    return out_vidpath, out_csvpath

def EstimateDepth(
        root,
        left_filename, 
        right_filename  
            ):
    left_filepath = os.path.join(root, left_filename)
    right_filepath = os.path.join(root, right_filename)
    out_vidpath = os.path.join(root, f'depth.avi')
    print(left_filepath, right_filepath)

    cap_left = cv2.VideoCapture(left_filepath)
    cap_right = cv2.VideoCapture(right_filepath)

    capw  = int(cap_left.get(cv2.CAP_PROP_FRAME_WIDTH))   # float `width`
    caph = int(cap_left.get(cv2.CAP_PROP_FRAME_HEIGHT))   # float `height`
    capfps = int(cap_left.get(cv2.CAP_PROP_FPS))          # FPS
    out = cv2.VideoWriter(out_vidpath, cv2.VideoWriter_fourcc('M','J','P','G'), capfps, (capw,caph))
    stereo = cv2.StereoBM_create(numDisparities=16, blockSize=15)

    while(True):
        ls, lframe = cap_left.read()
        rs, rframe = cap_right.read()
        if ls and rs:
            lfgray = cv2.cvtColor(lframe, cv2.COLOR_BGR2GRAY)
            rfgray = cv2.cvtColor(rframe, cv2.COLOR_BGR2GRAY)
            disparity = stereo.compute(lfgray,rfgray)
            out.write(disparity)
        else:
            break

    cap_left.release()
    cap_right.release()
    out.release()

    return out_vidpath


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('source',help='The footage that needs to have the cursor estimated on.')
    parser.add_argument('events',help='The CSV file generated from the vr simulation that contains eye positions')
    parser.add_argument('mapping',help='The mapping data that contains estimations of anchor positions')    
    parser.add_argument('frame_timestamps',help='The CSV file that contains the timestamps of each frame')
    args = parser.parse_args()

    EstimateCursor(args.source, args.events, args.mapping, args.frame_timestamps)