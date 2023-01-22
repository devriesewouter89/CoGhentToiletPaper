import cv2


def record_image(output_path):
    cam = cv2.VideoCapture(0)
    ret, image = cam.read()
    cv2.imwrite(output_path, image)
    cam.release()


def capture_image():
    cam = cv2.VideoCapture(0)
    ret, image = cam.read()
    cam.release()
    return image
