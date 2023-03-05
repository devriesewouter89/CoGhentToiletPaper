#!/usr/bin/python3

import os
import time

import cv2
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder

from config_toilet import get_git_root, Config


def create_template(img: str):
    '''
    This code will first convert the template image to grayscale, which is necessary for some image processing operations.
    It will then apply a bilateral filter to the grayscale image to improve the contrast and remove noise.
    Finally, it will threshold the filtered image to create a binary image, which is a simple representation of the template
    image with only two pixel values (0 and 255).

    You can adjust the parameters of the bilateral filter and the thresholding operation to suit the specific needs of your
    template image. For example, you may need to adjust the values of sigmaColor and sigmaSpace in the call
    to cv2.bilateralFilter to achieve the desired level of noise reduction. Similarly, you may need to adjust the
    value of threshold in the call to cv2.threshold to achieve the desired level of binarization.
    @param img:
    @return:
    '''

    # define the region of interest
    roi = create_region_of_interest(img, "template creation")

    # crop the image
    cropped_template = cropped_img_via_roi(img, roi)

    # Convert the template image to grayscale
    gray_template = cv2.cvtColor(cropped_template, cv2.COLOR_BGR2GRAY)

    # Apply image filtering to improve the contrast and remove noise
    filtered_template = cv2.bilateralFilter(gray_template, 2, 25, 75)

    # Threshold the image to create a binary image
    ret, thresh = cv2.threshold(filtered_template, 180, 255, cv2.THRESH_BINARY)

    # Display the result
    # cv2.imshow('cropped template', cropped_template)
    # cv2.imshow('gray_template', gray_template)
    # cv2.imshow('filtered_template', filtered_template)
    # cv2.imshow('thresh', thresh)
    cv2.imwrite('template.jpg', thresh)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return thresh


def test_roi():
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
    cv2.destroyAllWindows()


def cropped_img_via_roi(img, roi):
    '''
    crop an image
    @param img:
    @param roi:
    @return:
    '''
    # Read image
    im = cv2.imread(img)
    # Crop image
    imCrop = im[int(roi[1]):int(roi[1] + roi[3]), int(roi[0]):int(roi[0] + roi[2])]
    return imCrop


def create_region_of_interest(img, window_name: str = ""):
    # Read image
    im = cv2.imread(img)

    # Select ROI
    r = cv2.selectROI(window_name, im)
    return r


def save_region_of_interest(config_path: str, region_of_interest):
    with open(config_path, 'r', encoding='utf-8') as file:
        data = file.readlines()
    line_to_change = None
    for idx, i in enumerate(data):
        if "region_of_interest" in i:
            line_to_change = idx

    print(data)
    data[line_to_change] = "    region_of_interest = {}".format(region_of_interest)

    with open(config_path, 'w', encoding='utf-8') as file:
        file.writelines(data)


def return_matched_image(input_image, template, min_height=0, max_height=3840):
    input_image = cv2.imread(input_image,0)
    cv2.imshow("input normal", input_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    # # todo change with roi
    input_image = input_image[min_height: max_height, 0: input_image.shape[1]]
    # cv2.imshow("input cropped", input_image)
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
    print("coordinates of max loc: {}".format(max_loc))
    # Display the result
    # cv2.imshow('template', template)
    # cv2.imshow('input', cv2.resize(input_image, (int(input_image.shape[1]*0.6), int(input_image.shape[0]*0.6)),
    #                                interpolation=cv2.INTER_LINEAR))
    # cv2.imshow('cropped', cropped)
    return overlay, max_loc


def open_stream_until_OK(template, region_of_ok):
    # Encode a VGA stream, and capture a higher resolution still image half way through.

    picam2 = Picamera2()
    half_resolution = [dim // 2 for dim in picam2.sensor_resolution]
    main_stream = {"size": half_resolution}
    lores_stream = {"size": (640, 480)}
    video_config = picam2.create_video_configuration(main_stream, lores_stream, encode="lores")
    picam2.configure(video_config)

    encoder = H264Encoder(10000000)
    print("ready for recording")
    picam2.start_recording(encoder, 'test.h264')
    time.sleep(2)
    result = "NOK"
    while (result == "NOK"):
        # It's better to capture the still in this thread, not in the one driving the camera.
        request = picam2.capture_request()
        request.save("main", "test.jpg")
        result = qualify_position("test.jpg", template, region_of_ok)
        
        request.release()
        print("Still image captured!")

    # time.sleep(5)
    picam2.stop_recording()


def qualify_position(input_image, template, region_of_ok):
    overlay, max_loc = return_matched_image(input_image, template)
    # cv2.imshow("overlay", cv2.resize(overlay, (int(overlay.shape[1] * 0.6), int(overlay.shape[0] * 0.6))))
    # cv2.waitKey(0)
    # print("region of ok {}".format(region_of_ok))
    if region_of_ok[0] < max_loc[0] < region_of_ok[0] + region_of_ok[2]:
        print("OK")
        return "OK"
    else:
        print("Not OK")
        return "NOK"


def prepare(git_path: str):
    # create template
    template = create_template(os.path.join(git_path,
                                            'physical_control/toilet_paper_placement_indicator/template_matching/frames/plexi/backlit/OK/284.png'))
    region_of_ok = create_region_of_interest(os.path.join(git_path,
                                                          'physical_control/toilet_paper_placement_indicator/template_matching/frames/plexi/backlit/OK/294.png'),
                                                          "region of ok")
    config_path = os.path.join(git_path, "config_toilet.py")

    save_region_of_interest(config_path, region_of_ok)
    return template, region_of_ok


'''
This code will perform template matching using the method cv2.TM_CCOEFF_NORMED, which computes the normalized 
cross-correlation between the template and the input image. It will then find the coordinates of the best match 
and extract the region of the input image that contains the notch. Finally, it will display the template, 
the input image, and the cropped region containing the notch.
'''

if __name__ == '__main__':
    config = Config()
    template, region_of_ok = prepare(get_git_root(os.getcwd()))

    # Load the template image and the input image
    region_of_ok = config.region_of_interest

    manual = False
    if (manual == True):
        template = cv2.imread('template.jpg', 0)
        # img_path = Path(Path.cwd().parent / "training_init_toilet_roll" / "too_far")
        # img_path = './frames/backlit/NF/0056.png'
        img_path = './frames/plexi/backlit/NF/032.png'
        #
        input_image = cv2.imread(img_path, 0)
        overlay, max_loc = return_matched_image(input_image, template)
        cv2.imshow("overlay", cv2.resize(overlay, (int(overlay.shape[1] * 0.6), int(overlay.shape[0] * 0.6))))
        cv2.waitKey(0)
        print("region of ok {}".format(region_of_ok))
        if region_of_ok[0] < max_loc[0] < region_of_ok[0] + region_of_ok[2]:
            print("OK")
        else:
            print("Not OK")
    else:
        open_stream_until_OK(template, region_of_ok)
# TODO compare with next methods, perhaps these are better?
# https://github.com/cozheyuanzhangde/Invariant-TemplateMatching
# https://github.com/DennisLiu1993/Fastest_Image_Pattern_Matching
