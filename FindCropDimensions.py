import os
import numpy as np
import cv2
import argparse

# Argument parser - the user must specify the image to use
parser = argparse.ArgumentParser()
parser.add_argument('source', help="The image to use.")
parser.add_argument('-p', '--preview', default=False, help="Should we render the preview of the cutted image?")
args = parser.parse_args();

# Read the image in grayscale
src_raw = cv2.imread(args.source)
src_gray = cv2.cvtColor(src_raw, cv2.COLOR_BGR2GRAY)

# Need to detect the rightmost true white x-coordinate
# For the moment, '242' is the most ocmmon white value. You'll have to find a way to determine this yourself.
white_pixels = np.array(np.where(src_gray == 242))
min_x = min(white_pixels[1])
max_x = max(white_pixels[1])

# Based on the rightmost white pixel, we have to extract the leftmost crop amount
src_shape = np.shape(src_gray)
right_crop = src_shape[1]-max_x
new_min_x = min_x - right_crop

# Based on these, we will have to crop the image accordingly
crop = src_raw[:,new_min_x:]
crop_shape = np.shape(crop)

# Print the results
dirname = os.path.dirname(args.source)
basename = os.path.basename(args.source)
filename = os.path.splitext(basename)[0]
results_filename = os.path.join(dirname,filename+".txt")
# If the filename exists alreayd, delete it.
if os.path.exists(results_filename):
    os.remove(results_filename)
with open(results_filename, 'a') as file:
    file.write(f'Left_crop: {new_min_x}\n')
    file.write('Crop range:\n')
    file.write(f'\tX: {new_min_x} - {src_shape[1]}\n')
    file.write(f'\tY: 0 - {src_shape[0]}\n')
    file.write(f'Cropped image shape: {np.shape(crop)}')

print(f'For file "{args.source}":')
print(f'Left_crop: {new_min_x}')
print('Crop range:')
print(f'\tX: {new_min_x} - {src_shape[1]}')
print(f'\tY: 0 - {src_shape[0]}')
print(f'cropped image shape: {np.shape(crop)}')
print(f'Results stored in "{results_filename}"')

if (args.preview):
    cv2.imshow("hello", crop)
    cv2.waitKey(0)
    cv2.destroyAllWindows()