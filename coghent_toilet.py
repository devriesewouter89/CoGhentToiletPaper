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
from finite_state_machine.exceptions import InvalidStartState

from config_toilet import Config
from dBPathFinder.findOverlap import find_tree
from dBPathFinder.scripts.supabase_link import link_supabase, get_sb_data
from imageConversion.image_conversion import convert_folder_to_linedraw, create_in_between_images, \
    download_images_from_tree
from physical_control.paper_control import StepperControl
from physical_control.suction import SuctionControl
from print_timeline.print_timeline import TimelinePrinter

"""
#todo write documentation


"""


class ToiletPaperStateMachine(StateMachine):
    initial_state = "waiting"

    def __init__(self, config):
        self.config = config
        self.state = self.initial_state
        super().__init__()
        self.df_tree = None
        self.stepperControl = StepperControl()
        self.sc = SuctionControl()
        self.timeline = TimelinePrinter()
        self.image_number = 0
        self.finished = False

    @transition(source="waiting", target="path_finding")
    def find_path(self):
        """

        we find a possible path for this run and generate the csvs for this
        """
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
        self.df_tree = pd.read_csv(config.tree_path, index_col=0)

    @transition(source=["path_finding", "test_df"], target="prep_imgs")
    def prep_imgs(self):
        """
        1. we download the images for this tree
        2. we create the in-between pages
        3. we convert the images to lineart
        """

        # 1.
        download_images_from_tree(df=self.df_tree,
                                  output_path=config.tree_img_path)
        print("images downloaded")
        # 2.
        create_in_between_images(df=self.df_tree, output_path=config.in_between_page_path)
        print("in beteen images created")
        # 3.
        convert_folder_to_linedraw(input_path=config.tree_img_path,
                                   output_path=config.converted_img_path,
                                   draw_hatch=False,
                                   draw_contour=True,
                                   contour_simplify=2,
                                   hatch_size=24)
        print("images converted to lineart")

    @transition(source="prep_imgs", target="prep_timeline")
    def prep_timeline(self):
        list1 = self.timeline.get_list_of_files(config.converted_img_path)
        list2 = self.timeline.get_list_of_files(config.in_between_page_path)
        self.timeline.create_comb_list(list1, list2)

    @transition(source=["prep_timeline", "print_img"], target="roll_paper")
    def roll_paper(self):
        # ! bijhouden hoeveel we afrollen
        self.stepperControl.roll_towards_next_sheet()

    @transition(source="roll_paper", target="print_img")
    def print_img(self):
        # 1. start suction
        self.sc.enable_suction()
        # 2. start printing
        self.timeline.plot_img_from_list(self.image_number)
        # 3. disable suction
        self.sc.disable_suction()
        # 4. update the image number if finished
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


if __name__ == '__main__':
    print("starting the coghent toilet paper printer software")
    # read config file
    config = Config()
    # TODO add a physical setup function: find height of pen etc

    stm = ToiletPaperStateMachine(config)
    stm.test_df()
    stm.prep_imgs()
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
