from pyaxidraw import axidraw
import sys
import os  # if you want this directory
import git
from pathlib import Path

from sshkeyboard import listen_keyboard


def get_project_root():
    return Path(git.Repo('.', search_parent_directories=True).working_tree_dir)


try:
    sys.path.index(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
from config_toilet import Config


def set_axi_options(ad: axidraw.AxiDraw, config: Config):
    ad.options.pen_pos_up = config.pen_pos_up
    ad.options.pen_pos_down = config.pen_pos_down
    ad.options.speed_pendown = config.speed_pendown
    ad.options.model = config.model
    ad.options.reordering = config.reordering


def plot(svg_file, config):
    ad = axidraw.AxiDraw()
    ad.plot_setup(svg_file)
    set_axi_options(ad, config)
    ad.plot_run()


def calibrate_heights(config):
    ad = axidraw.AxiDraw()
    ad.plot_setup()
    ad.options.mode = "cycle"
    ad.options.pen_pos_up = config.pen_pos_up
    ad.options.pen_pos_down = config.pen_pos_down
    print(config.pen_pos_up, config.pen_pos_down)
    ad.plot_run()


def disable_axidraw():
    ad = axidraw.AxiDraw()
    ad.plot_setup()
    ad.options.mode = "align"
    ad.plot_run()


def on_press(key):
    try:
        print('alphanumeric key {0} pressed'.format(
            key))
        if key == "q":
            config.pen_pos_up += 2
            calibrate_heights(config)
        if key == "e":
            config.pen_pos_up -= 2
            calibrate_heights(config)
        if key == "a":
            config.pen_pos_down += 2
            calibrate_heights(config)
        if key == "d":
            config.pen_pos_down -= 2
            calibrate_heights(config)
        if key == "s":  # save
            print("adapt the config_toilet.py file with :")
            print("\t pen_pos_up = {}".format(pen_pos_up))
            print("\t pen_pos_down = {}".format(pen_pos_down))
        if key =='p': #plot test file
            plot("test_output_cairo.svg", config)
        if key =='h': # halt the steppers for the axidraw
            disable_axidraw()
    except AttributeError:
        print('special key {0} pressed'.format(
            key))


if __name__ == '__main__':
    global pen_pos_up, pen_pos_down
    config = Config()

    listen_keyboard(on_press=on_press)