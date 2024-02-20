import os
import argparse
import subprocess
import json
import cv2
import csv
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument('input', help='the relative path to the video in question')
args = parser.parse_args()

input_dir = os.path.dirname(args.input)
input_basename = os.path.splitext(os.path.basename(args.input))[0]
output_dir = os.path.join(input_dir, input_basename+"_timestamps")
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("====================")
print("PARSING VIDEO FRAMES AND FRAMERATE")
print(f"Video to Process: {args.input}")
print("====================")

# ------------------------------------------------------------------------------

cmd_str = f"ffprobe -loglevel error -select_streams v:0 -show_entries packet=pts_time,flags -of json {args.input}"
output = json.loads(subprocess.check_output(cmd_str, shell=True).decode('utf-8'))
output_timestamps = [float(packet['pts_time']) for packet in output['packets']]
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
print(f"# Frames Detected: {len(output_timestamps)}")
plt.plot(timestamp_deltas, c='b')
plt.title("Timestamp Deltas")
plt.xlabel("Frame #")
plt.ylabel("Time Between Frames (sec)")
plt.savefig(os.path.join(output_dir,"timestamp_deltas.png"))
#plt.show()
print(f"Output saved in {output_dir}")

#cap = cv2.VideoCapture(args.input)
#n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#print(n_frames)

#cmd_str = f"ffmpeg -i {args.input} -vf vfrdet -an -f null -"
#output = subprocess.check_output(cmd_str, shell=True).decode('utf-8')
#print(output)