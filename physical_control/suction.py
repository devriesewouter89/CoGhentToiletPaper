#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import sys
import os  # if you want this directory

try:
    sys.path.index(os.path.join(os.environ["HOME"], "CoGhentToiletPaper"))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(os.path.join(os.environ["HOME"], "CoGhentToiletPaper"))  # Or os.getcwd() for this directory
from config_toilet import Config


class SuctionControl:
    def __init__(self, config: Config):
        self.suction_GPIO = config.suction_GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.suction_GPIO, GPIO.OUT)

    def test_suction(self):
        for i in range(10):
            print("high")
            GPIO.output(self.suction_GPIO, GPIO.HIGH)
            time.sleep(4)
            print("low")
            GPIO.output(self.suction_GPIO, GPIO.LOW)
            time.sleep(4)

    def enable_suction(self):
        GPIO.output(self.suction_GPIO, GPIO.HIGH)

    def disable_suction(self):
        GPIO.output(self.suction_GPIO, GPIO.LOW)


if __name__ == '__main__':
    config = Config()
    sc = SuctionControl(config)
    sc.test_suction()
