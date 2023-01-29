from pyaxidraw import axidraw

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
    ad.plot_run()


def disable_axidraw():
    ad = axidraw.AxiDraw()
    ad.plot_setup()
    ad.options.mode = "align"
    ad.plot_run()


if __name__ == '__main__':
    config = Config()
    calibrate_heights(config)
    # plot("test_output_cairo.svg")
