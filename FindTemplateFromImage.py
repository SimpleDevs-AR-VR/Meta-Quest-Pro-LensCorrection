import numpy as np
import argparse
import cv2

parser = argparse.ArgumentParser()
parser.add_argument('source',help="The source video that contains the template yo're looking for")
parser.add_argument('template',help="The template image to search for")
args = parser.parse_args()

img = cv2.imread(args.source)
img_h, img_w, _ = img.shape
template_all = cv2.imread(args.template, cv2.IMREAD_UNCHANGED)

min_dim = min(img_h, img_w)
boxes = []
for p in np.arange(10,int(min_dim/3),5):
    print(f"template size: {p}")
    template_resize = cv2.resize(template_all, (p,p))
    template = template_resize[:,:,0:3]
    alpha = template_resize[:,:,3]
    alpha = cv2.merge([alpha,alpha,alpha])
    h,w = template.shape[:2]

    loc = []
    res = cv2.matchTemplate(
        img,
        template,
        cv2.TM_CCORR_NORMED,
        mask=alpha
    )
    loc = np.where(res >= 0.90)
    if len(loc) > 0:
        for pt in zip(*loc[::-1]):
            boxes.append((pt[0],pt[1],pt[0]+w,pt[1]+h))

result = img.copy()
for (x1, y1, x2, y2) in boxes:
    result = cv2.rectangle(result, (x1, y1), (x2, y2),(23,255,255), 1)

cv2.imshow('template',result)
cv2.waitKey(0)
cv2.destroyAllWindows()