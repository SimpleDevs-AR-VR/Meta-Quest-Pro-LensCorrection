import numpy as np
import os
import argparse
import cv2

parser = argparse.ArgumentParser()
parser.add_argument('source',help="The source video that contains the template yo're looking for")
parser.add_argument('template',help="The template image to search for")
args = parser.parse_args()

pred_dir = os.path.dirname(args.source)
pred_dirname = os.path.splitext(os.path.basename(args.source))[0]
pred_output_filename = os.path.join(pred_dir, pred_dirname+'_pred.avi')
if os.path.exists(pred_output_filename):
    os.remove(pred_output_filename)

template_all = cv2.imread(args.template, cv2.IMREAD_UNCHANGED)

cap = cv2.VideoCapture(args.source)
capfps = cap.get(cv2.CAP_PROP_FPS)
caph = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
capw = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
capl = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
min_dim = min(caph, capw)
output = cv2.VideoWriter(pred_output_filename,cv2.VideoWriter_fourcc(*'MJPG'),capfps,(int(capw),int(caph)))
output_window = "Eye Track Test"
cv2.namedWindow(output_window)

frame_counter = 0
while cap.isOpened():
    # Read a frame from the video
    success, frame = cap.read()
    frame_counter += 1
    print(f"Current Frame: {frame_counter}/{capl}")
    # Only continue if successful
    if success:
        boxes = []
        for p in np.arange(10,int(min_dim/3),5):
            template_resize = cv2.resize(template_all, (p,p))
            template = template_resize[:,:,0:3]
            alpha = template_resize[:,:,3]
            alpha = cv2.merge([alpha,alpha,alpha])
            h,w = template.shape[:2]
            loc = []
            res = cv2.matchTemplate(
                frame,
                template,
                cv2.TM_CCORR_NORMED,
                mask=alpha
            )
            loc = np.where(res >= 0.90)
            if len(loc) > 0:
                for pt in zip(*loc[::-1]):
                    boxes.append((pt[0],pt[1],pt[0]+w,pt[1]+h))

        result = frame.copy()
        for (x1, y1, x2, y2) in boxes:
            result = cv2.rectangle(result, (x1, y1), (x2, y2),(23,255,255), 1)
        cv2.imshow(output_window, result)
        output.write(result)

        if cv2.waitKey(1) & 0xFF == 27:
            break

output.release() 
cap.release() 
cv2.destroyAllWindows()