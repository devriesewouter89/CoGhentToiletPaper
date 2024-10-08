"""Simple test for using adafruit_motorkit with a stepper motor"""
import argparse
import sys
import time
from pathlib import Path

import board
import git
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit
from sshkeyboard import listen_keyboard

from config_toilet import Config
from physical_control.suction import SuctionControl
from physical_control.toilet_paper_placement_indicator.template_matching import CamControl, SheetPlacement, PLACEMENT


def get_project_root():
    return Path(git.Repo('.', search_parent_directories=True).working_tree_dir)


try:
    sys.path.index(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(str(get_project_root().resolve()))  # Or os.getcwd() for this directory


class StepperControl:
    def __init__(self, config: Config):
        """
        """
        self.kit = MotorKit(i2c=board.I2C(), address=config.stepperi2c) #todo
        self.total_roll = 0
        self.placement = PLACEMENT.NOT_FAR
        self.config = config
        self.cc = CamControl(config)
        self.sheet = SheetPlacement(self.cc, config)

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

    def calibrate_template_matching(self):
        self.sheet.prepare()

    def move_paper_right(self, amount_of_steps: int = 50):
        """
        for some reason, I need to direct both steppers in order to be able to pull back the paper
        @param amount_of_steps:
        @return:
        """
        self.total_roll -= amount_of_steps
        self.kit.stepper1.release()
        for _ in range(amount_of_steps):
           #self.kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
           self.kit.stepper2.onestep(direction=stepper.BACKWARD) #, style=stepper.SINGLE)
        # todo necessary to have both activated afterwards so paper can't move?

    def move_paper_left(self, amount_of_steps: int = 50):
        """

        @param amount_of_steps:
        @return:
        """
        self.total_roll += amount_of_steps
        self.kit.stepper2.release()
        for _ in range(amount_of_steps):
            self.kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
            #self.kit.stepper2.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
        # todo necessary to have both activated afterwards so paper can't move?
        #time.sleep(1.0)


    def roll_towards_next_sheet(self):
        """

        @return:
        """
        self.placement = PLACEMENT.NOT_FAR
        # # 1. first we move the paper a little bit
        # self.move_paper_left(amount_of_steps=20)
        # 1. the idea is that first we have to move from PLACEMENT.CORRECT towards PLACEMENT.NOT_FAR ( with a bool)
        # and onlya
        # then start listening again to PLACEMENT.CORRECT
        # 2. we go and check the position
        self.cc.start_vid_rec()

        paper_has_left_original_position = False
        paper_has_left_original_position_threshold = self.config.move_paper_threshold # amount of frames before deciding we really left the original position
        while True:
            # It's better to capture the still in this thread, not in the one driving the camera.
            self.cc.capture_during_rec()
            self.placement = self.sheet.qualify_position(str(self.config.temp_img.resolve()), self.sheet.template,
                                                         self.sheet.region_of_ok)
            print('placement : {}'.format(self.placement))
            if self.placement == PLACEMENT.CORRECT:
                print("found correct location")
                if paper_has_left_original_position:
                    break
                else:
                    #we need to get the paper first far enough to start measuring again
                    self.move_paper_left(amount_of_steps=5)
                    continue
            if self.placement == PLACEMENT.TOO_FAR:
                self.move_paper_right(amount_of_steps=5)
                continue
            if self.placement == PLACEMENT.NOT_FAR:
                if paper_has_left_original_position_threshold <=0:
                    paper_has_left_original_position = True
                paper_has_left_original_position_threshold -= 1
                self.move_paper_left(amount_of_steps=5)
                continue
        self.cc.stop_vid_rec()

    def insert_sshkeyboard(self):
        print("inserting ssh keyboard")
        listen_keyboard(on_press=self.on_press, until="space", debug=True)

    def on_press(self, key):
        try:
            print('alphanumeric key {0} pressed'.format(
                key))
            if key == "a":
                self.move_paper_left(50)
            if key == "d":
                self.move_paper_right(50)
            if key == "r":  # release
                self.kit.stepper1.release()
                self.kit.stepper2.release()
            if key == "t":
                self.roll_towards_next_sheet()
            # if key == "w":
            #     sc.disable_suction()
            if key == "o":
                print("paper is aligned correctly")
                self.placement = PLACEMENT.CORRECT
        except AttributeError:
            print('special key {0} pressed'.format(
                key))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='paper control',
        description="a script to move the paper and to check if it's positioned correctly",
        epilog="it's all about the toilet paper")
    parser.add_argument('-i', '--interactive',
                        action='store_true', help='interactive usage')  # on/off flag

    args = parser.parse_args()
    config = Config()
    stepperControl = StepperControl(config)

    # Collect events until released
    if args.interactive:
        stepperControl.insert_sshkeyboard()
