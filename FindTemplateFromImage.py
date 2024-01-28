import numpy as np
import argparse
import cv2

def FindTemplateMatch(
        frame, 
        template_filename, 
        min_size=10, 
        max_size=50, 
        delta_size=5, 
        thresh=0.9,
        draw_bbox=False,
        draw_centers=False,
        bbox_color=[0,255,255],
        bbox_thickness=1,
        verbose=False):
    # Load template using opencv
    template_all = cv2.imread(template_filename, cv2.IMREAD_UNCHANGED)
    # Prep boxes list
    boxes = []
    # Iterate through possible sizes of the template, upwards to half of the size
    for p in np.arange(min_size, max_size, delta_size):
        # Resize the frame
        template_resize = cv2.resize(template_all, (p,p))
        # Get particular attributes of the image itself. 
        # We assume transparency, so we have to separate alpha from bgr
        template = template_resize[:,:,0:3]
        alpha = template_resize[:,:,3]
        alpha = cv2.merge([alpha,alpha,alpha])
        # get the width and height of the template
        h,w = template.shape[:2]
        # Prepare possible locations where the template matches
        loc = []
        # Find those matches.
        res = cv2.matchTemplate(
            frame,
            template,
            cv2.TM_CCORR_NORMED,
            mask=alpha
        )
        # threshold by a 
        loc = np.where(res >= thresh)
        if len(loc) > 0:
            for pt in zip(*loc[::-1]):
                boxes.append((pt[0],pt[1],pt[0]+w,pt[1]+h, pt[0]+(w/2), pt[1]+(h/2)))

    
    centers = []
    for (x1, y1, x2, y2, cx, cy) in boxes:
        #result = cv2.rectangle(result, (x1, y1), (x2, y2), bbox_color, bbox_thickness)
        centers.append([cx,cy])

    mean_center = np.mean(centers, axis=0)
    median_center = np.median(centers, axis=0)
    
    if verbose:
        print(f"ESTIMATED MEAN POSITION: {mean_center}")
        print(f"ESTIMATED MEDIAN POSITION: {median_center}")
    
    if draw_bbox or draw_centers:
        result = frame.copy()
        if draw_bbox:
             for (x1, y1, x2, y2, cx, cy) in boxes:
                 result = cv2.rectangle(result, (x1, y1), (x2, y2), bbox_color, bbox_thickness)
        if draw_centers:
            result = cv2.drawMarker(result, (int(mean_center[0]), int(mean_center[1])), (0,255,255),cv2.MARKER_CROSS,20,2)
            result = cv2.drawMarker(result, (int(median_center[0]), int(median_center[1])), (255,255,0),cv2.MARKER_TILTED_CROSS,20,2)
        return mean_center, median_center, result
    
    return mean_center, median_center

def main(args):
    img = cv2.imread(args.source)
    img_h, img_w, _ = img.shape
    min_dim = min(img_h, img_w)
    mean_center, median_center, result = FindTemplateMatch(img, args.template, thresh=args.threshold, draw_centers=True, verbose=True)
    cv2.imshow('Template Match', result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('source',help="The source video that contains the template yo're looking for")
    parser.add_argument('template',help="The template image to search for")
    parser.add_argument('-t', '--threshold',
                        help='The threshold of confidence for if a possible detection ought to be considered',
                        type=float,
                        default=0.9)
    parser.add_argument('-c', '--color',
                        help='Color of detection bounding box',
                        nargs='+',
                        type=int,
                        default=[0,255,255])
    args = parser.parse_args()
    main(args)