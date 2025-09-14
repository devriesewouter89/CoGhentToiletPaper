from pyaxidraw import axidraw
import sys
import git
from pathlib import Path

from sshkeyboard import listen_keyboard


def get_project_root():
    return Path(git.Repo('', search_parent_directories=True).working_tree_dir)


try:
    sys.path.index(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
from src.config_toilet import Config


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

def move_to_start_offset(config):
    ad = axidraw.AxiDraw()
    ad.interactive()                # Enter interactive context
    if not ad.connect():            # Open serial port to AxiDraw;
        quit()                      #   Exit, if no connection.
                                    # Absolute moves follow:
    ad.moveto(config.paper_offset[0],config.paper_offset[1])  # Pen-up move, to starting offset.
    disable_axidraw()
    ad.disconnect()                 # Close serial port to AxiDraw

def disable_axidraw():
    ad = axidraw.AxiDraw()
    ad.plot_setup()
    ad.options.mode = "align"
    ad.plot_run()

def return_home():
    ad = axidraw.AxiDraw()
    ad.interactive()                # Enter interactive context
    if not ad.connect():            # Open serial port to AxiDraw;
        quit()                      #   Exit, if no connection.
                                    # Absolute moves follow:
    ad.moveto(0, 0)                 # Pen-up move, back to origin.
    disable_axidraw()
    ad.disconnect()                 # Close serial port to AxiDraw


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
            print("\t pen_pos_up = {}".format(config.pen_pos_up))
            print("\t pen_pos_down = {}".format(config.pen_pos_down))
        if key =='p': #plot test file
            plot("calibrate.svg", config)
        if key =='x': # halt the steppers for the axidraw
            disable_axidraw()
        if key == 'h':
            return_home()
        if key =='c': # test the calibration file
            plot("calibrate.svg", config)
        if key =='m':
            move_to_start_offset(config)

    except AttributeError:
        print('special key {0} pressed'.format(
            key))
        raise SystemExit


if __name__ == '__main__':
    print("q/e is pen pos up +/-, a/d is pen pos down +/-, s is save, p is plot, h is halt the steppers")
    global pen_pos_up, pen_pos_down
    config = Config()
    
    listen_keyboard(on_press=on_press)
