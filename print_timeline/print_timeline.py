import itertools
from natsort import natsorted
import sys
import os  # if you want this directory
import git
from pathlib import Path


def get_project_root():
    return Path(git.Repo('.', search_parent_directories=True).working_tree_dir)


try:
    sys.path.index(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
from config_toilet import Config

from pyaxidraw import axidraw


class TimelinePrinter:
    def __init__(self, config):
        try:
            self.ad = axidraw.AxiDraw()
        except Exception as e:
            print(e)
        self.comb_list = []
        self.config = config

    def create_comb_list(self, list1, list2):
        """
        creates an alternating list:
        list1 = [A, B]
        list2 = [C, D]
        ==> comb_list = [A, C, B, D]
        @param list1:
        @param list2:
        @return:
        """
        temp = itertools.zip_longest(list1, list2)
        self.comb_list = [x for x in itertools.chain.from_iterable(temp) if x]
        return self.comb_list

    def move_to_start_offset(self):
        ad = axidraw.AxiDraw()
        ad.interactive()  # Enter interactive context
        if not ad.connect():  # Open serial port to AxiDraw;
            quit()  # Exit, if no connection.
            # Absolute moves follow:
        ad.moveto(self.config.paper_offset[0], self.config.paper_offset[1])  # Pen-up move, to starting offset.
        self.disable_axidraw()
        ad.disconnect()

    def disable_axidraw(self):
        ad = axidraw.AxiDraw()
        ad.plot_setup()
        ad.options.mode = "align"
        ad.plot_run()

    def get_list_of_files(self, dir_name: str):
        """
        create a **sorted** list of file and subdirectories names in the given directory

        @param dir_name:
        @return:
        """
        list_of_file = os.listdir(dir_name)
        list_of_file = natsorted(list_of_file)
        all_files = list()
        # Iterate over all the entries
        for entry in list_of_file:
            # Create full path
            full_path = os.path.join(dir_name, entry)
            # If entry is a directory then get the list of files in this directory
            if os.path.isdir(full_path):
                all_files = all_files + self.get_list_of_files(full_path)
            else:
                all_files.append(full_path)
        return all_files

    def plot_img_from_list(self, index: int = 0):
        img = self.comb_list[index]
        # self.ad.moveto(config.paper_offset)
        self.ad = axidraw.AxiDraw()
        self.ad.plot_setup(img)
        self.ad.options.pen_pos_up = self.config.pen_pos_up
        self.ad.options.pen_pos_down = self.config.pen_pos_down
        self.ad.plot_run()
        # try:
        # output_svg = self.ad.plot_run(True)
        # except KeyboardInterrupt:
        # print("exiting the plotting par user request")
        # self.ad.plot_setup(output_svg)
        # self.ad.options.mode = "res_home"
        # output_homed = self.ad.plot_run(True)
        # raise SystemExit

    def test_paper_startingpoint(self):
        self.ad.interactive()
        self.ad.options.pen_pos_up = 70  # set pen-up position
        if not self.ad.connect():  # Open serial port to AxiDraw;
            quit()  # Exit, if no connection.

        self.ad.moveto(config.paper_offset[0], config.paper_offset[1])
        input("push a button to return to base")
        self.ad.moveto(0, 0)
        self.ad.disconnect()  # Close serial port to AxiDraw

    def test_paper_startingpoint(self):
        self.ad.interactive()
        self.ad.options.pen_pos_up = 70  # set pen-up position
        if not self.ad.connect():  # Open serial port to AxiDraw;
            quit()  # Exit, if no connection.

        self.ad.moveto(config.paper_offset[0], config.paper_offset[1])
        input("push a button to return to base")
        self.ad.moveto(0, 0)
        self.ad.disconnect()  # Close serial port to AxiDraw

    def get_img(self, index):
        return self.comb_list[index]


if __name__ == '__main__':
    config = Config()
    tp = TimelinePrinter(config)
    # 1. create list of images
    list1 = tp.get_list_of_files(config.converted_img_path)
    list2 = tp.get_list_of_files(config.in_between_page_path)
    res = tp.create_comb_list(list1, list2)
    print(res)
    tp.test_paper_startingpoint()
#    tp.plot_img_from_list(0)
