import time

import cv2
from pathlib import Path


def return_matched_image(input_image, template, min_height=0, max_height=3840):
    cv2.imshow("input normal", input_image)

    input_image = input_image[min_height: max_height, 0 : input_image.shape[1]]
    cv2.imshow("input cropped", input_image)
    # Perform template matching
    result = cv2.matchTemplate(input_image, template, cv2.TM_CCOEFF_NORMED)

    # Find the coordinates of the best match
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Extract the region of the input image that contains the notch
    h, w = template.shape
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    cropped = input_image[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
    overlay = cv2.rectangle(input_image.copy(), max_loc, (max_loc[0] + w, max_loc[1] + h), (0, 0, 255), 2)
    # Display the result
    # cv2.imshow('template', template)
    # cv2.imshow('input', cv2.resize(input_image, (int(input_image.shape[1]*0.6), int(input_image.shape[0]*0.6)),
    #                                interpolation=cv2.INTER_LINEAR))
    # cv2.imshow('cropped', cropped)
    return overlay


'''
This code will perform template matching using the method cv2.TM_CCOEFF_NORMED, which computes the normalized 
cross-correlation between the template and the input image. It will then find the coordinates of the best match 
and extract the region of the input image that contains the notch. Finally, it will display the template, 
the input image, and the cropped region containing the notch.
'''

if __name__ == '__main__':
    # Load the template image and the input image
    template = cv2.imread('thresh_template.jpg', 0)
    img_path = Path(Path.cwd().parent / "training_init_toilet_roll" / "too_far")

    input_image = cv2.imread(str(Path(img_path / '5.JPEG')), 0)
    overlay = return_matched_image(input_image, template, 800, 1500)
    cv2.imshow("overlay", cv2.resize(overlay, (int(overlay.shape[1] * 0.6), int(overlay.shape[0] * 0.6))))
    cv2.waitKey(0)

# TODO compare with next methods, perhaps these are better?
# https://github.com/cozheyuanzhangde/Invariant-TemplateMatching
# https://github.com/DennisLiu1993/Fastest_Image_Pattern_Matching