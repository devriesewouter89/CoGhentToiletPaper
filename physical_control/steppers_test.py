# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""Simple test for using adafruit_motorkit with a stepper motor"""
import time
import board
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
from sshkeyboard import listen_keyboard


class StepperControl:
    def __init__(self):
        """
        """
        self.kit = MotorKit(i2c=board.I2C())
        self.total_roll = 0

    def test_stepper(self):
        for _ in range(10):
            for _ in range(100):
                self.kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
                self.kit.stepper2.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
            time.sleep(1.0)
            for _ in range(100):
                self.kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
                self.kit.stepper2.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
            time.sleep(1.0)
        self.kit.stepper1.release()
        self.kit.stepper2.release()

    def move_paper_left(self, amount_of_steps: int = 50):
        """

        @param amount_of_steps:
        @return:
        """
        self.total_roll += amount_of_steps
        self.kit.stepper2.release()
        for _ in range(amount_of_steps):
#            self.kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
            self.kit.stepper2.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
        # todo necessary to have both activated afterwards so paper can't move?

    def move_paper_right(self, amount_of_steps: int = 50):
        """

        @param amount_of_steps:
        @return:
        """
        self.total_roll -= amount_of_steps
        self.kit.stepper1.release()
        for _ in range(amount_of_steps):
            self.kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
            #self.kit.stepper2.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
        # todo necessary to have both activated afterwards so paper can't move?




def on_press(key):
    try:
        print('alphanumeric key {0} pressed'.format(
            key))
        if key == "q":
            stepperControl.move_paper_left(50)
        if key == "d":
            stepperControl.move_paper_right(50)
    except AttributeError:
        print('special key {0} pressed'.format(
            key))


if __name__ == '__main__':
    stepperControl = StepperControl()
    # Collect events until released
    listen_keyboard(on_press=on_press)
