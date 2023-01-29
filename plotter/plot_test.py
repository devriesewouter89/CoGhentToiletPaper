from pyaxidraw import axidraw
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


if __name__ == '__main__':
    config = Config()
#    disable_axidraw()
    calibrate_heights(config)
    # plot("test_output_cairo.svg")
