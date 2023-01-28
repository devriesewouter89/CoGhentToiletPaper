#!/usr/bin/python3

import RPi.GPIO as GPIO
import time

class SuctionControl:
    def __init__(self):
        self.suction_GPIO = 8

        GPIO.setmode(GPIO.BOARD)
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

# GPIO.cleanup()

if __name__ == '__main__':
    sc = SuctionControl()
    sc.test_suction()