 SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""Simple test for using adafruit_motorkit with a stepper motor"""
import time
import board
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

kit = MotorKit(i2c=board.I2C())
for i in range(10):
    for i in range(100):
        kit.stepper1.onestep(direction=stepper.FORWARD, style= stepper.SINGLE)
        kit.stepper2.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
    time.sleep(1.0)
    for i in range(100):
        kit.stepper1.onestep(direction=stepper.BACKWARD, style= stepper.SINGLE)
        kit.stepper2.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
    time.sleep(1.0)
kit.stepper1.release()
kit.stepper2.release()

#for i in range(1000):
#    kit.stepper1.onestep()
#    kit.stepper2.onestep()
