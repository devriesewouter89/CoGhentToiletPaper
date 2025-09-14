#!/usr/bin/python3
import sys
import time
from pathlib import Path

import RPi.GPIO as GPIO
import git


def get_project_root():
    return Path(git.Repo('.', search_parent_directories=True).working_tree_dir)


try:
    sys.path.index(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
from src.config_toilet import Config


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
