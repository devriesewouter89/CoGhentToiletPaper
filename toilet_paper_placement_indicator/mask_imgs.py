import cv2
import numpy as np
from pathlib import Path


def detect_black_lines(img, scale: int = None):
    img = cv2.imread(img)

    if scale != None:
        width = int(img.shape[1] * scale / 100)
        height = int(img.shape[0] * scale / 100)
        dim = (width, height)

        img = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)

    # Cropping an image
    img = img[0:img.shape[0]-120, 40:img.shape[1]]

    # median blur
    median = cv2.medianBlur(img, 5)

    # threshold on black
    threshold = 100
    lower = (0, 0, 0)
    upper = (threshold, threshold, threshold)
    thresh = cv2.inRange(median, lower, upper)

    # apply morphology open and close
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (29, 29))
    morph = cv2.morphologyEx(morph, cv2.MORPH_CLOSE, kernel)

    # filter contours on area
    contours = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]
    result = img.copy()
    for c in contours:
        area = cv2.contourArea(c)
        if area > 1000:
            cv2.drawContours(result, [c], -1, (0, 0, 255), 2)

    # view result
    cv2.imshow("threshold", thresh)
    cv2.imshow("morphology", morph)
    cv2.imshow("result", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def create_mask(black_img):
    # read a completely black image
    img = cv2.imread(black_img)

    points_left = np.array([
        [160, 130],
        [350, 130],
        [250, 300]
    ])

    points_right = np.array([
        [360, 130],
        [250, 130],
        [150, 300]
    ])

    cv2.fillPoly(img, pts=[points_left, points_right], color=(255, 0, 0))

    cv2.imshow("Two polygons", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # create_mask("mask.png")
    img = Path(Path.cwd() / "camera_calibration" / "2.jpg")
    print(img)
    if img.is_file():
        detect_black_lines(str(img))
