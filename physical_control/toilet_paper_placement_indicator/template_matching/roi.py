import os

import cv2
import numpy as np


def cropped_img_via_roi(img, roi):
    # Read image
    im = cv2.imread(img)
    # Crop image
    imCrop = im[int(roi[1]):int(roi[1] + roi[3]), int(roi[0]):int(roi[0] + roi[2])]
    return imCrop


def create_region_of_interest(img):
    # Read image
    im = cv2.imread(img)

    # Select ROI
    r = cv2.selectROI(im)
    return r


if __name__ == '__main__':
    img = os.path.join(os.getcwd(), "../1.jpg")
    print(img)
    roi = create_region_of_interest(img)
    imCrop = cropped_img_via_roi(img, roi)
    # Display cropped image
    cv2.imshow("Image", imCrop)
    cv2.waitKey(0)
    # test roi on other images:
    img2 = os.path.join(os.getcwd(), "../2.jpg")
    imCrop = cropped_img_via_roi(img2, roi)
    # Display cropped image
    cv2.imshow("Image", imCrop)
    cv2.waitKey(0)
