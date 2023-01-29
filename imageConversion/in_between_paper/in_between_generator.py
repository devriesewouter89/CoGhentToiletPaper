#!/usr/bin/env python
import os
import numpy as np
import svglue
import drawSvg as draw
import textwrap
from typing import Union
import cairo
import git
from pathlib import Path
import sys

def get_project_root():
    return Path(git.Repo('.', search_parent_directories=True).working_tree_dir)


try:
    sys.path.index(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
from config_toilet import Config
from pycairo_arcs import *


def wrap_text_if_needed(ctx, text: str, max_width_text: int, max_height_text: int) -> Union[str, list[str]]:
    """

    @param text: text to wrap and cut off if necessary
    @param max_width_text: amount of characters
    @param max_height_text: amount of lines
    @return: the original string if cutoff is not needed, otherwise a list of strings
    """
    x_off, y_off, text_width, text_height, dx, dy = ctx.text_extents(text)
    # we have [text_width] for [len(text)] amount of characters, thus we want our wrapper to cut off at:
    # tot#char * allowed_width / total_width
    max_characters = math.floor(len(text) * max_width_text / text_width)
    wrapper = textwrap.TextWrapper(width=max_characters)
    word_list = wrapper.wrap(text)
    if len(word_list) > max_height_text:
        word_list = word_list[:max_height_text]
        word_list.append("...")
    return word_list


def limit_overlap_text(overlap_list: list[str], max_lines: int = 3):
    if len(overlap_list) > max_lines:
        overlap_list = overlap_list[:max_lines]
    return overlap_list


def text(ctx, string, pos, angle=0.0, face='Georgia', font_size=18):
    ctx.save()

    # build up an appropriate font
    ctx.select_font_face(face, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(font_size)
    fascent, fdescent, fheight, fxadvance, fyadvance = ctx.font_extents()
    x_off, y_off, text_width, text_height, dx, dy = ctx.text_extents(string)
    nx = -text_width / 2.0
    ny = fheight / 2
    ctx.translate(pos[0], pos[1])
    ctx.rotate(np.radians(angle))
    ctx.translate(nx, ny)
    ctx.move_to(0, 0)
    ctx.show_text(string)
    ctx.restore()


def create_svg_cairo(title_old: str, text_old: str, year_old: str, title_new: str, text_new: str, year_new: str,
                     overlap_text: Union[str, list[str]], config: Config,
                     output_path: Path, percentage_of_layers: float, max_width_text: int = 40,
                     max_height_text: int = 4):
    surface = cairo.SVGSurface(str(output_path), config.sheet_width,
                               config.sheet_height)
    surface.set_document_unit(cairo.SVGUnit.MM)
    cr = cairo.Context(surface)
    # TEXT PARAMETERS & PLACEMENT VALUES
    cr.select_font_face("Sans",
                        cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_NORMAL)
    offset_x_text = 25
    offset_x_title = 10
    angle_offset = 20
    angle = percentage_of_layers * 2 * angle_offset - angle_offset  # function to make diagonal "move" throughout time
    radius = (config.sheet_width / 2 - offset_x_text) * 0.6
    cr.set_line_width(0.1)

    # --------background color for development---------
    cr.set_source_rgb(100.0, 0.0, 0.0)
    cr.rectangle(0, 0, config.sheet_width, config.sheet_height)
    cr.fill()
    # -----------------OLD TEXT -----------------------
    cr.set_source_rgb(0, 0, 0)
    # adapt the width of the text
    text_old = wrap_text_if_needed(cr, text_old, max_width_text, max_height_text)
    # Draw text
    for idx, i in enumerate(text_old):
        text(cr, i, (offset_x_text - idx * config.font_size, config.sheet_height / 2), angle=90,
             font_size=config.font_size)
    # -----------------OLD TITLE -----------------------
    text(cr, title_old, (offset_x_title, config.sheet_height / 2), angle=90, font_size=config.font_size + 2)
    # # -----------------NEW TEXT-----------------------
    # adapt the width of the text
    text_new = wrap_text_if_needed(cr, text_new, max_width_text, max_height_text)
    # Draw text
    for idx, i in enumerate(text_new):
        text(cr, i, (config.sheet_width - offset_x_text + idx * config.font_size, config.sheet_height / 2), angle=270,
             font_size=config.font_size)
    # -----------------NEW TITLE-----------------------
    text(cr, title_new, (config.sheet_width - offset_x_title, config.sheet_height / 2), angle=270,
         font_size=config.font_size + 2)
    cr.fill()
    # --------------CENTER CIRCLE FIGURE--------------
    # circle
    cr.arc(config.sheet_width / 2.0, config.sheet_height / 2.0, radius, 0, 2 * math.pi)
    cr.stroke()
    # moving lines
    cr.move_to(config.sheet_width / 2 + math.sin(np.radians(angle)) * radius,
               config.sheet_height / 2 + math.cos(np.radians(angle)) * radius)
    cr.line_to(config.sheet_width / 2 + math.tan(np.radians(angle)) * config.sheet_height / 2.0, config.sheet_height)
    cr.stroke()
    cr.move_to(config.sheet_width / 2 - math.sin(np.radians(angle)) * radius,
               config.sheet_height / 2 - math.cos(np.radians(angle)) * radius)
    cr.line_to(config.sheet_width / 2 - math.tan(np.radians(angle)) * config.sheet_height / 2.0, 0)
    cr.stroke()

    # text path
    # p = draw.Path(stroke='none', stroke_width=2, fill='none')
    overlap_text = limit_overlap_text(overlap_text)
    for idx, i in enumerate(overlap_text):
        cr.set_font_size(config.circle_fontsize)
        _text = wrap_text_if_needed(cr, i, 40, 1)
        text(cr, _text[0],
             (config.sheet_width / 2,
              config.sheet_height / 2 -
              (len(overlap_text) - 1) / 2.0 * config.circle_fontsize * 1.1 + idx * config.circle_fontsize * 1.1),
             0,
             font_size=config.circle_fontsize)
    # place the years on the circle as well
    cr.set_font_size(config.year_fontsize)
    text_arc_path(cr, config.sheet_width / 2.0, config.sheet_height / 2.0, year_old, radius + 0.5,
                  np.radians(140 - angle))
    cr.fill()
    text_arc_path(cr, config.sheet_width / 2.0, config.sheet_height / 2.0, year_new, radius + 0.5, np.radians(angle))
    cr.fill()
    surface.write_to_png("{}.png".format(os.path.splitext(output_path)[0]))


def adapt_svg_for_print(d: draw):
    """
    for printing, our in-between images are not suited due to some small issues:
    - svg dimensions aren't specified for mm or inches
    - text should be converted to path objects
    """
    d.width = "{}mm".format(d.width)
    d.height = "{}mm".format(d.height)
    return d


if __name__ == '__main__':
    config = Config()
    create_svg_cairo("titel", "vorige wc-rol met veel meer tekst dan de lijn toelaat", "2000", "titel",
                     "volgende wc-rol",
                     "2001",
                     ["wc-rol", "test", "3"], config=config, output_path=Path("test_output_cairo.svg"),
                     percentage_of_layers=0, max_width_text=100, max_height_text=2)
