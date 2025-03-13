"""""""""""""""
This file intends to extract frame numbers from video images, based off of footage recorded from Unity, 
and overlap that footage with estimated eye tracking data. This is intended to correct for
all the oddities involved with attempting an automated method using Unity's `WorldToScreenPoint`.
This assumes that you have a video feed with the frame number from Unity somewhere in the footage,
a mappings file that defines a transformation matrix to map from screen point to corrected screen point,
and a CSV file that contains the world to screen point data from Unity.

The method to do this involves interpreting from image-to-text what frame in Unity the current video frame is depicting.
The python package we will be relying on is EasyOCR: https://github.com/JaidedAI/EasyOCR
Make sure to follow installation instructions on the github repo's README before doing anything.

The file allows you to use a function `EstimateEyeCursor`, which should output a video file with the 
eye tracking data from Unity overlapped on top of each frame. It also extracts a CSV containing each video frame's
corresponding frame number in Unity, using EasyOCR to extract that number from the frame. There are also some 
additional things you can do, such as extract the frames as images too.

Note that the eye tracking CSV data from unity contains the following columns:
- unix_ms
- rel_timestamp
- frame <-- UNITY FRAME
- event <-- EYE HIT
- side <-- LEFT, RIGHT, or CENTER
- screen_pos_x <-- X
- screen_pos_y <-- Y
- screen_pos_z
- target_name
"""""""""""""""

import numpy as np
import json
import pandas as pd

import os
from pathlib import Path

import cv2 as cv
import easyocr

import argparse

# This needs to be run only one, in order to load the model into memory.
# We are telling it to run on the english language.
reader = easyocr.Reader(['en'])

# Helper function: is this an Integer?
def check_int(s:str):
    try: int(s)
    except ValueError: return False
    else: return True

# Main function definition
def EstimateCursor(
        video_filepath:str, 
        events_filepath:str,
        mapping_filepath:str, 
        output_dir:str,

        offset_seconds:float = 0,
        video_output_filename:str = 'output',
        csv_output_filename:str = 'frames'):    

    # If we want to save the output video, CSV, and images, we need an output dir. 
    # Thus, we need to check if it exists already and empty it.
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)
        try:
            if os.path.isfile(filepath) or os.path.islink(filepath):
                os.unlink(filepath)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (filepath, e))
    if video_output_filename is None or len(video_output_filename)==0:
        video_output_filename = os.path.splitext(os.path.basename(video_filepath))[0]
    vid_outpath = os.path.join(output_dir, video_output_filename+'.avi')

    # Initialize mappings json, and get the transformation matrices
    with open(mapping_filepath) as jsonfile:
        mapping = json.load(jsonfile)
    transformation_matrix = np.array(mapping['transformation_matrix'])

    # Define a nested function that returns the transformed point, provided the transformation matrix
    def transform(input):
        A = np.array(input + [1])
        return np.dot(A,transformation_matrix)
    
    # Read the events filepath from Unity, extract only the relevant eye cursor data
    # Assume we want the left eye
    events_df = pd.read_csv(events_filepath)
    eye_df = events_df[events_df['side']=='Left']

    # Initialize OpenCV-Python to begin extracting frames
    vidcap = cv.VideoCapture(video_filepath)
    vidcapw  = int(vidcap.get(cv.CAP_PROP_FRAME_WIDTH))   # float `width`
    vidcaph = int(vidcap.get(cv.CAP_PROP_FRAME_HEIGHT))   # float `height`
    vidcapfps = int(vidcap.get(cv.CAP_PROP_FPS))          # FPS
    out = cv.VideoWriter(vid_outpath, cv.VideoWriter_fourcc('M','J','P','G'), vidcapfps, (vidcapw,vidcaph))
    success, image = vidcap.read()
    count = 0
    offset_frames = vidcapfps * offset_seconds

    # Loop!
    while success:
        # We check if count exceeds the provided offset, which is set to a default frame offset of 30
        if count > offset_frames:

            # Make a copy of the frame
            result = np.copy(image)

            # Attempt to grayscale and apply threshold for easier frame processing
            gry = cv.cvtColor(result, cv.COLOR_BGR2GRAY)
            thr = cv.threshold(gry, 100, 255, cv.THRESH_BINARY)[1]

            # Attempt to extract text. If detected, proceed
            screen_text = reader.readtext(thr)
            if len(screen_text) > 0:
                # Get the most confident text, which should be the clearest. Check if it's an integer
                conf_text = screen_text[0][1]
                if check_int(conf_text):
                    # Get the eye rows that represent this frame
                    eye_rows = eye_df.loc[eye_df['frame'] == int(conf_text)]
                    if not eye_rows.empty:
                        # Iterate through rows, attempting to apply the correction matrix and pasting on to the screen
                        for index, row in eye_rows.iterrows():
                            eye_pos_est = transform([row['screen_pos_x'], row['screen_pos_y']])
                            eye_pos = (int(eye_pos_est[0]), int(vidcaph-eye_pos_est[1])) # flip the Y
                            #result = cv.drawMarker(result, eye_pos, (255,0,0), cv.MARKER_CROSS, 20, 2)
                            result = cv.rectangle(
                                result,
                                (eye_pos[0] - 10, eye_pos[1] - 10),
                                (eye_pos[0] + 10, eye_pos[1] + 10),
                                (255,0,0), 3)

            # Write the final frame to the output video
            out.write(result)

        # Get the next frame
        success, image = vidcap.read()
        count += 1

    # Finally, close the video capture and output
    vidcap.release()
    out.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # REQUIRED
    parser.add_argument('source',help='The footage that needs to have the cursor estimated on.')
    parser.add_argument('events',help='The CSV file generated from the vr simulation that contains eye positions')
    parser.add_argument('mapping',help='The mapping data that contains estimations of anchor positions')
    parser.add_argument('output_dir',help='The output directory')

    # OPTIONAL
    parser.add_argument('-ofs','--offset_seconds',help='How many seconds from the beginning should we initially ignore?', type=float, default=0)
    parser.add_argument('-outf','--output_filename',help='The output filename, no extension needed', type=str, default='')

    args = parser.parse_args()

    EstimateCursor(
        args.source, 
        args.events, 
        args.mapping, 
        args.output_dir, 
        
        offset_seconds=args.offset_seconds, 
        video_output_filename=args.output_filename)

"""
import os
import subprocess
import json
import cv2
import csv
import matplotlib.pyplot as plt

def ExtractTimestamps(input_vid, offset_ts=0.0, save_fig=False, verbose=False):
    input_dir = os.path.dirname(input_vid)
    input_basename = os.path.splitext(os.path.basename(input_vid))[0]
    output_dir = os.path.join(input_dir, input_basename+"_timestamps") if save_fig else input_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if verbose:
        print("====================")
        print("PARSING VIDEO FRAMES AND FRAMERATE")
        print(f"Video to Process: {input_vid}")
        print("====================")

    cmd_str = f"ffprobe -loglevel error -select_streams v:0 -show_entries packet=pts_time,flags -of json {input_vid}"
    output = json.loads(subprocess.check_output(cmd_str, shell=True).decode('utf-8'))
    output_timestamps = [float(packet['pts_time']) - offset_ts for packet in output['packets']]
    output_timestamps = sorted(output_timestamps)
    timestamp_deltas = [output_timestamps[i]-output_timestamps[i-1] for i in range(1, len(output_timestamps))]
    timestamp_deltas.insert(0, 0.0)
    csv_outfile = os.path.join(output_dir, "frame_timestamps.csv")
    csv_timestamp_fields = ['frame','timestamp','time_delta']
    with open(csv_outfile, 'w', newline='') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile) 
        # writing the fields
        csvwriter.writerow(csv_timestamp_fields)
        for i in range(len(output_timestamps)):
            csvwriter.writerow([i, output_timestamps[i], timestamp_deltas[i]]) 
    if verbose:
        print(f"# Frames Detected: {len(output_timestamps)}")

    if save_fig:
        plt.plot(timestamp_deltas, c='b')
        plt.title("Timestamp Deltas")
        plt.xlabel("Frame #")
        plt.ylabel("Time Between Frames (sec)")
        plt.savefig(os.path.join(output_dir,"timestamp_deltas.png"))
    
    if verbose:
        print(f"Output saved in {output_dir}")
    
    return csv_outfile

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='the relative path to the video in question')
    parser.add_argument('-o', '--offset', 
                        help='If needed, an offset timestamp (in seconds) after the video starts',
                        type=float,
                        default=0.0)
    parser.add_argument('-sf', '--save_fig', 
                        help="Should we store a figure of all the frame-to-frame time deltas too?", 
                        action="store_true")
    parser.add_argument('-v', '--verbose', 
                        help="Should we print statements verbosely?",
                        action="store_true")
    args = parser.parse_args()
    output_file = ExtractTimestamps(args.input, offset_ts=args.offset, save_fig=args.save_fig, verbose=args.verbose)
    print(f"Timestamps saved as: {output_file}")




# ------------------------------------------------------------------------------



#cap = cv2.VideoCapture(args.input)
#n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#print(n_frames)

#cmd_str = f"ffmpeg -i {args.input} -vf vfrdet -an -f null -"
#output = subprocess.check_output(cmd_str, shell=True).decode('utf-8')
#print(output)
"""