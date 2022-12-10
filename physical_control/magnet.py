#!/usr/bin/python3

import RPi.GPIO as GPIO
import time

magnet = 8

GPIO.setmode(GPIO.BOARD)
GPIO.setup(magnet, GPIO.OUT)

for i in range(10):
    GPIO.output(magnet, GPIO.HIGH)
    time.sleep(4)
    GPIO.output(magnet, GPIO.LOW)
    time.sleep(4)

GPIO.cleanup()
