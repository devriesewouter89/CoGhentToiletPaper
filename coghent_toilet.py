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
import pandas as pd
from finite_state_machine import StateMachine, transition

from config_toilet import Config
from dBPathFinder.findOverlap import find_tree
from dBPathFinder.scripts.supabase_link import link_supabase, get_sb_data
from imageConversion.image_conversion import convert_folder_to_linedraw, create_in_between_images, \
    download_images_from_tree
from physical_control.keypad_controller import KeypadController
from physical_control.paper_control import StepperControl
from physical_control.suction import SuctionControl
from print_timeline.print_timeline import TimelinePrinter
from plotter.plot_test import return_home

"""
#todo write documentation


"""


class ToiletPaperStateMachine(StateMachine):
    initial_state = "waiting"

    def __init__(self, config, key):
        self.config = config
        self.state = self.initial_state
        super().__init__()  # init only to be called after setting self.state
        self.df_tree = None
        self.stepperControl = StepperControl(config=config)
        self.timeline = TimelinePrinter(config=config)

        self.key = key
        self.key.set_message(0, "hello toilet printer fellow!")
        self.image_number = 0
        self.finished = False

    @transition(source="waiting", target="path_finding")
    def find_path(self):
        """

        we find a possible path for this run and generate the csvs for this
        """
        self.key.set_message(0, "searching a path")
        # 1. Make connection with supabase database
        sb = link_supabase(config)
        # 2. fetch the dataframe for current location
        input_df = get_sb_data(sb, config.location)
        # 3. find the tree path
        self.df_tree = find_tree(input_df=input_df,
                                 output_file=config.tree_path,
                                 stemmer_cols=config.stemmer_cols,
                                 list_cols=config.list_cols,
                                 amount_of_imgs_to_find=config.amount_of_imgs_to_find)

    @transition(source="waiting", target="test_df")
    def test_df(self):
        self.key.set_message(0, "testing a path")

        self.df_tree = pd.read_csv(config.tree_path, index_col=0)

    @transition(source=["path_finding", "test_df"], target="prep_imgs")
    def prep_imgs(self):
        """
        1. we download the images for this tree
        2. we create the in-between pages
        3. we convert the images to lineart
        """
        self.key.set_message(0, "prepping imgs")

        # 1.
        download_images_from_tree(df=self.df_tree,
                                  output_path=config.tree_img_path)
        print("images downloaded")
        # 2.
        create_in_between_images(df=self.df_tree, output_path=config.in_between_page_path, config=config)
        print("in beteen images created")
        # 3.
        convert_folder_to_linedraw(input_path=config.tree_img_path,
                                   output_path=config.converted_img_path,
                                   config=config)
        print("images converted to lineart")

    @transition(source=["prep_imgs", "waiting"], target="prep_timeline")
    def prep_timeline(self):
        self.key.set_message(0, "timeline")

        list1 = self.timeline.get_list_of_files(config.converted_img_path)
        list2 = self.timeline.get_list_of_files(config.in_between_page_path)
        self.timeline.create_comb_list(list1, list2)

    @transition(source=["prep_timeline"], target="move_to_start_pos")
    def move_to_start_pos(self):
        self.timeline.move_to_start_offset()
        self.key.set_message(0,"moving to start")

    @transition(source=["move_to_start_pos", "prep_timeline", "print_img"], target="roll_paper")
    def roll_paper(self):
        self.key.set_message(0, "roll it!")

        print("preparing sheet {} for {}".format(self.image_number, self.timeline.get_img(self.image_number)))
        # ! bijhouden hoeveel we afrollen
        self.stepperControl.roll_towards_next_sheet()

    @transition(source="roll_paper", target="print_img")
    def print_img(self):
        print("plotting image {}".format(self.image_number))
        self.key.set_messages("print it!", "img {}".format(self.image_number))
        # 1. move to start position
        # 
        # 2. start printing
        self.timeline.plot_img_from_list(self.image_number)
        # 3. update the image number if finished
        if self.image_number < self.config.amount_of_tissues:
            self.image_number += 1
        else:
            self.finished = True

    @transition(source="print_img", target="roll_back_paper")
    def roll_back(self):
        self.stepperControl.move_paper_right(self.stepperControl.total_roll)
        # todo check if we're not pulling too far?

    @transition(source="roll_back_paper", target="waiting")
    def wait(self):
        self.finished = False
        pass


 # def read_lcd_buttons(self, channel):
 #     #todo: adapt this for having a menu switching option, perhaps link directly to the wanted functions?
 #        # switch between modes
 #        if channel == 17:
 #            print(self.btnUP)
 #            self.mode = key.Mode((self.mode.value + 1) % 4)
 #        if channel == 18:
 #            print(self.btnDOWN)
 #            self.mode = key.Mode((self.mode.value - 1) % 4)
 #
 #        if self.mode == key.Mode.SETUP:
 #            self.set_message(0, "SETUP")
 #            if channel == 16:
 #                print(self.btnSELECT)
 #            if channel == 19:
 #                print(self.btnLEFT)
 #                self.blink(2.0)
 #            if channel == 20:
 #                print(self.btnRIGHT)
 #                # self.breath(0x02)  # 0x03 red 0x02
 #                return key.Functions.calibrate
 #        if self.mode == Mode.ROLL:
 #            self.set_message(0, "ROLL")
 #            if channel == 16:
 #                print(self.btnSELECT)
 #            if channel == 19:
 #                print(self.btnLEFT)
 #                return Functions.roll_left
 #            if channel == 20:
 #                print(self.btnRIGHT)
 #                return Functions.roll_right
 #        if self.mode == Mode.TEST:
 #            self.set_message(0, "TEST")
 #            if channel == 16:
 #                print(self.btnSELECT)
 #            if channel == 19:
 #                print(self.btnLEFT)
 #                self.blink(2.0)
 #            if channel == 20:
 #                print(self.btnRIGHT)
 #                # self.breath(0x02)  # 0x03 red 0x02
 #                return Functions.test
 #        if self.mode == Mode.PROGRESS:
 #            self.set_message(0,"PROGRESS")
 #            if channel == 20:
 #                return Functions.progress



if __name__ == '__main__':
    print("starting the coghent toilet paper printer software")
    # read config file
    config = Config()
    # TODO add a physical setup function: find height of pen etc
    key = KeypadController()
    key.add_event_function(key.btnRIGHT.get("GPIO"), key.read_lcd_buttons)
    key.add_event_function(key.btnLEFT.get("GPIO"), key.read_lcd_buttons)
    key.add_event_function(key.btnUP.get("GPIO"), key.read_lcd_buttons)
    key.add_event_function(key.btnDOWN.get("GPIO"), key.read_lcd_buttons)
    stm = ToiletPaperStateMachine(config, key)

# #TODO put in calibration mode?
#     stm.stepperControl.calibrate_template_matching()


    try:
        # stm.test_df()
        # stm.prep_imgs()
        stm.prep_timeline()
        while not stm.finished:
            stm.roll_paper()
            stm.print_img()
        stm.roll_back()
        stm.wait()
        # stm.find_path()
        # print("finished path creation")
        # stm.prep_imgs()
        # for i in range(0, 49):
        #     stm.roll_paper()
        #     stm.print_img()
        # stm.roll_back()
        # stm.wait()
        # try:
        #     stm.print_img()  # should trigger an error
        # except InvalidStartState as e:
        #     print("Error: {}".format(e))
    except KeyboardInterrupt:
        print("exiting the program par user request")
        return_home()
        raise SystemExit


