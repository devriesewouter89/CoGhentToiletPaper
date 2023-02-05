"""Simple test for using adafruit_motorkit with a stepper motor"""
import sys
import time
from time import sleep
from pathlib import Path

import board
import git
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit
from sshkeyboard import listen_keyboard

from config_toilet import Config
from physical_control.suction import SuctionControl


def get_project_root():
    return Path(git.Repo('.', search_parent_directories=True).working_tree_dir)


try:
    sys.path.index(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
from physical_control.toilet_paper_placement_indicator.sheet_placement import PLACEMENT


class StepperControl:
    def __init__(self):
        """
        """
        self.kit = MotorKit(i2c=board.I2C())
        self.total_roll = 0
        self.placement = PLACEMENT.NOT_FAR

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
            self.kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
            # self.kit.stepper2.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
        # todo necessary to have both activated afterwards so paper can't move?

    def move_paper_right(self, amount_of_steps: int = 50):
        """

        @param amount_of_steps:
        @return:
        """
        self.total_roll -= amount_of_steps
        self.kit.stepper1.release()
        for _ in range(amount_of_steps):
            # self.kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
            self.kit.stepper2.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
        # todo necessary to have both activated afterwards so paper can't move?

    def roll_towards_next_sheet(self):
        """

        @return:
        """
        # 1. first we move the paper a little bit
        self.move_paper_left(amount_of_steps=50)
        # 2. then we go and check the position
        if self.placement != PLACEMENT.CORRECT:
            # if sheet_placement() == PLACEMENT.CORRECT:
            #     break
            # if sheet_placement() == PLACEMENT.TOO_FAR:
            #     self.move_paper_right(amount_of_steps=10)
            # if sheet_placement() == PLACEMENT.NOT_FAR:
            #     self.move_paper_left(amount_of_steps=10)
            self.insert_sshkeyboard()

    def insert_sshkeyboard(self):
        listen_keyboard(on_press=self.on_press, until="space")


    def on_press(self, key):
        try:
            print('alphanumeric key {0} pressed'.format(
                key))
            if key == "a":
                self.move_paper_left(50)
            if key == "d":
                self.move_paper_left(50)
            # if key == "s":
            #     sc.enable_suction()
            # if key == "w":
            #     sc.disable_suction()
            if key == "o":
                print("paper is aligned correctly")
                self.placement = PLACEMENT.CORRECT
        except AttributeError:
            print('special key {0} pressed'.format(
                key))


if __name__ == '__main__':
    config = Config()
    stepperControl = StepperControl()
    sc = SuctionControl(config)

    # Collect events until released
    stepperControl.insert_sshkeyboard()
