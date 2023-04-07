import math
from pathlib import Path
from time import sleep

import cv2 as cv
import numpy as np


def show_lines_in_file(file):
    img = cv.imread(file)
    # Window name in which image is displayed
    window_name = 'image'
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    sobel = cv.Sobel(gray, ddepth=cv.CV_64F, dx=1, dy=0, ksize=11)
    laplacian = cv.Laplacian(gray, cv.CV_64F)

    # Setting parameter values
    t_lower = 50  # Lower Threshold
    t_upper = 150  # Upper threshold
    aperture_size = 3
    L2Gradient = True  # Boolean

    edges = cv.Canny(gray, t_lower, t_upper, apertureSize=aperture_size)#, L2gradient=L2Gradient)

    # cv.imshow(window_name, gray)
    # cv.waitKey(0)
    # cv.imshow(window_name, sobel)
    # cv.waitKey(0)
    # cv.imshow(window_name, laplacian)
    # cv.waitKey(0)
    cv.imshow(window_name, edges)
    cv.waitKey(0)

    lines = cv.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=100)
    if lines is not None:
        for i in range(0, len(lines)):
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * (a)))
            pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * (a)))
            cv.line(gray, pt1, pt2, (0, 0, 255), 3, cv.LINE_AA)

    cv.imshow(window_name, gray)
    cv.waitKey(0)

    cv.imwrite('houghlines3.jpg', img)
    cv.destroyAllWindows()

DEFAULT_TEMPLATE_MATCHING_THRESHOLD = 0.5


class Template:
    """
    A class defining a template
    """
    def __init__(self, image_path, label, color, matching_threshold=DEFAULT_TEMPLATE_MATCHING_THRESHOLD):
        """
        Args:
            image_path (str): path of the template image path
            label (str): the label corresponding to the template
            color (List[int]): the color associated with the label (to plot detections)
            matching_threshold (float): the minimum similarity score to consider an object is detected by template
                matching
        """
        self.image_path = image_path
        self.label = label
        self.color = color
        self.template = cv.imread(image_path)
        self.template_height, self.template_width = self.template.shape[:2]
        self.matching_threshold = matching_threshold




def template_matching(img, template):
    detections = []
    cv.imshow('template', template.template)
    cv.waitKey(0)
    img = cv.imread(img)
    cv.imshow('img', img)
    cv.waitKey(0)
    # for template in templates:
    template_matching = cv.matchTemplate(
            img, template.template, cv.TM_CCOEFF_NORMED
        )

    match_locations = np.where(template_matching >= template.matching_threshold)

    for (x, y) in zip(match_locations[1], match_locations[0]):
        match = {
            "TOP_LEFT_X": x,
            "TOP_LEFT_Y": y,
            "BOTTOM_RIGHT_X": x + template.template_width,
            "BOTTOM_RIGHT_Y": y + template.template_height,
            "MATCH_VALUE": template_matching[y, x],
            "LABEL": template.label,
            "COLOR": template.color
        }

        detections.append(match)
    image_with_detections = img.copy()
    for detection in detections:
        cv.rectangle(
            image_with_detections,
            (detection["TOP_LEFT_X"], detection["TOP_LEFT_Y"]),
            (detection["BOTTOM_RIGHT_X"], detection["BOTTOM_RIGHT_Y"]),
            detection["COLOR"],
            2,
        )
        cv.putText(
            image_with_detections,
            f"{detection['LABEL']} - {detection['MATCH_VALUE']}",
            (detection["TOP_LEFT_X"] + 2, detection["TOP_LEFT_Y"] + 20),
            cv.FONT_HERSHEY_SIMPLEX,
            0.5,
            detection["COLOR"],
            1,
        cv.LINE_AA
        )
        cv.imshow('image', image_with_detections)
        cv.waitKey(0)

        # cv.imwrite(f"output/result.jpeg", image_with_detections)

if __name__ == '__main__':
    img = str(Path(Path.cwd() / "aligned" / "001.jpg").resolve())
    print(img)
    # show_lines_in_file(img)

    # templates = [
    #     Template(image_path="data/component1.jpg", label="1", color=(0, 0, 255)),
    #     Template(image_path="data/component2.jpg", label="2", color=(0, 255, 0)),
    #     Template(image_path="data/component3.jpg", label="3", color=(0, 191, 255)),
    # ]
    template = Template(image_path=str(Path(Path.cwd() / "aligned" / "template.jpg").resolve()), label="1", color=(0, 0, 255))
    template_matching(img, template)