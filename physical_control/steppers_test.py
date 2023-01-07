# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""Simple test for using adafruit_motorkit with a stepper motor"""
import time
import board
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
from pynput import keyboard


class stepperControl:
    def __init__(self):
        self.kit = MotorKit(i2c=board.I2C())

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
        for _ in range(amount_of_steps):
            self.kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
            self.kit.stepper2.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)

    def move_paper_right(self, amount_of_steps: int = 50):
        for _ in range(amount_of_steps):
            self.kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
            self.kit.stepper2.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)


def on_press(key):
    try:
        print('alphanumeric key {0} pressed'.format(
            key.char))
        if key.char == "q":
            stepperControl.move_paper_left(50)
        if key.char == "d":
            stepperControl.move_paper_left(50)
        if key.char == "l":
            print("bye")
    except AttributeError:
        print('special key {0} pressed'.format(
            key))


def on_release(key):
    print('{0} released'.format(
        key))
    if key == keyboard.Key.esc:
        # Stop listener
        return False


if __name__ == '__main__':
    stepperControl = stepperControl()
    # Collect events until released
    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()

    # ...or, in a non-blocking fashion:
    # listener = keyboard.Listener(
    #     on_press=on_press)
    # listener.start()
    # while True:
    #     if keyboard.read_key() == "q":
    #         print("You pressed 'q'.")
    #         stepperControl.move_paper_left(50)
    #         continue
    #     if keyboard.read_key() == "d":
    #         print("you pressed 'd'")
    #         stepperControl.move_paper_right(50)
    #         continue
    #     if keyboard.read_key() == "l":  # leave
    #         print("byebye")
    #         break
