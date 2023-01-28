from pathlib import Path
import os
import cv2
from matplotlib import pyplot as plt
import numpy as np


def renumber_training_data(path: Path):
    print("renaming {} files".format(len(os.listdir(path))))
    res = input("OK? Y[/N]")
    if res == "N":
        return
    for idx, _file in enumerate(os.listdir(path)):
        os.rename(os.path.join(path, _file), os.path.join(path, "{}.webp".format(idx)))


def edge_detection_sobel(img_path: str):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.GaussianBlur(gray, (3, 3), 0)
    sobelx = cv2.Sobel(src=img, ddepth=cv2.CV_64F, dx=1, dy=0, ksize=5)

    sobely = cv2.Sobel(src=img, ddepth=cv2.CV_64F, dx=0, dy=1, ksize=5)

    sobelxy = cv2.Sobel(src=img, ddepth=cv2.CV_64F, dx=1, dy=1, ksize=5)

    plt.figure(figsize=(18, 19))
    plt.subplot(221)
    plt.imshow(img, cmap='gray')
    plt.title('Original')
    plt.axis("off")

    plt.subplot(222)
    plt.imshow(sobelxy, cmap='gray')
    plt.title('Sobel X Y')
    plt.axis("off")

    plt.subplot(223)
    plt.imshow(sobelx, cmap='gray')
    plt.title('Sobel X')
    plt.axis("off")

    plt.subplot(224)
    plt.imshow(sobely, cmap='gray')
    plt.title('Sobel Y')
    plt.axis("off")
    plt.show()


def canny_edge_detection(img_path: str):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(image=img, threshold1=20, threshold2=40)

    plt.figure(figsize=(18, 19))
    plt.subplot(121)
    plt.imshow(img, cmap='gray')
    plt.title('Original')
    plt.axis("off")

    plt.subplot(122)
    plt.imshow(edges, cmap='gray')
    plt.title('Edge image')
    plt.axis("off")
    plt.show()


if __name__ == '__main__':
    # convert names in training dir
    training_dir = Path(os.path.join(os.getcwd(), "training_init_toilet_roll"))
    # for sub_path in os.listdir(training_dir):
    #     renumber_training_data(Path(training_dir / sub_path))

    # test out sobel edge detection
    img_path = Path(training_dir / "aligned" / "1.webp")
    print(img_path)
    # edge_detection_sobel(img_path=str(img_path))
    canny_edge_detection(img_path=str(img_path))