"""
Coghent toilet

we want a state machine calling the different blocks of code:
---PREPPING---
1. Waiting state:
    1. no toilet paper rol is present and is prepared
    2. or we've finished a toilet paper roll
    DEBUG: A **light** gives signal that we're in waiting state
    NEXT STATE: we wait for a switch to indicate that we're going to the next state
    ! 4 way switch: forward, backward, neutral, ready to start
2. we find the path in the database of the museum we are (via config file)
    NEXT STATE: once path is found,
    DEBUG ERROR: if not found ERROR LAMP Path
3. prepare toilet paper images:
    1. we download the images
    2. convert images to linedraw vectors in the correct size
    3. create in between pages
    4. place them altogether in folder
---PRINTING---
4. roll the toilet paper roll state:
    1. we start rolling the toilet paper (1 NEMA stepper motor with two GT2 pulleys and inbetween e.g. this belt: https://www.123-3d.nl/123-3D-GT2-timing-belt-6-mm-gesloten-848-mm-i2751-t3046.html)
        ! We keep track of the amount of rotations
    2. we rotate a little and then start checking the camera
    NEXT STATE: once position is correct
5. print the next prepared image
    NEXT STATE: if more images present => state 4 when image is finished
    NEXT STATE: if no more images present => state 6 when image is finished
6. roll back toilet paper state
    DEBUG: the waiting light is shown that we're ready
    We roll back the paper already a bit in approx of the amount of rotations already done
"""

import configparser

from finite_state_machine import StateMachine, transition
from finite_state_machine.exceptions import InvalidStartState

from config_toilet import Config
from dBPathFinder.findOverlap import find_tree

"""
#todo write documentation


"""


class ToiletPaperStateMachine(StateMachine):
    initial_state = "waiting"

    def __init__(self, config):
        self.config = config
        self.state = self.initial_state
        super().__init__()

    @transition(source="waiting", target="path_finding")
    def find_path(self):
        ftree = find_tree(input_file=config.clean_data_path,
                          output_file=config.tree_path,
                          stemmer_cols=config.stemmer_cols,
                          list_cols=config.list_cols,
                          amount_of_imgs_to_find=config.amount_of_imgs_to_find)

    @transition(source="path_finding", target="prep_imgs")
    def prep_imgs(self):
        pass

    @transition(source=["prep_imgs", "print_img"], target="roll_paper")
    def roll_paper(self):
        #! bijhouden hoeveel we afrollen
        pass

    @transition(source="roll_paper", target="print_img")
    def print_img(self):
        pass

    @transition(source="print_img", target="roll_back_paper")
    def roll_back(self):
        pass

    @transition(source="roll_back_paper", target="waiting")
    def wait(self):
        pass


if __name__ == '__main__':
    print("starting the coghent toilet paper printer software")
    # read config file
    config = Config()

    stm = ToiletPaperStateMachine(config)
    stm.find_path()
    print("finished path creation")
    stm.prep_imgs()
    for i in range(0, 49):
        stm.roll_paper()
        stm.print_img()
    stm.roll_back()
    stm.wait()
    try:
        stm.print_img()  # should trigger an error
    except InvalidStartState as e:
        print("Error: {}".format(e))
