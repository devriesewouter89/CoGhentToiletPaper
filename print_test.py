from pyaxidraw import axidraw
def plot(svg_file):
    ad = axidraw.AxiDraw()
    ad.plot_setup(svg_file)
    ad.options.pen_pos_up = 70
    ad.plot_run()


if __name__ == '__main__':
    plot("test_output_cairo.svg")
