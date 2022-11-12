import cv2
import numpy as np

def create_mask(black_img):
    # read a completely black image
    img = cv2.imread(black_img)

    points_left = np.array([
        [160,130],
        [350,130],
        [250,300]
    ])

    points_right = np.array([
        [360,130],
        [250,130],
        [150,300]
    ])

    cv2.fillPoly(img, pts=[points_left, points_right], color=(255,0,0))

    cv2.imshow("Two polygons", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    create_mask("mask.png")
