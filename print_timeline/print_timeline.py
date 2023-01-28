import itertools
import os
from natsort import natsorted
from config_toilet import Config
from pyaxidraw import axidraw


class TimelinePrinter:
    def __init__(self):
        try:
            self.ad = axidraw.AxiDraw()
        except Exception as e:
            print(e)
        self.comb_list = []

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
        self.ad.plot_setup(img)
        self.ad.options.pen_pos_up = 70
        self.ad.plot_run()


if __name__ == '__main__':
    config = Config()
    tp = TimelinePrinter()
    # 1. create list of images
    list1 = tp.get_list_of_files(config.converted_img_path)
    list2 = tp.get_list_of_files(config.in_between_page_path)
    res = tp.create_comb_list(list1, list2)
    print(res)
    tp.plot_img_from_list(0)
