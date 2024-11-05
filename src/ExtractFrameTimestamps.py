import os
import argparse
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