#!/usr/bin/env python
import os
import numpy as np
import svglue
# import drawSvg as draw
import textwrap
from typing import Union
import cairo
import git
from pathlib import Path
import sys
# from pycairo_arcs import *
import math

from imageConversion.in_between_paper.pycairo_arcs import text_arc_path


def get_project_root():
    return Path(git.Repo('.', search_parent_directories=True).working_tree_dir)


try:
    sys.path.index(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
from config_toilet import Config


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
    wrapper = textwrap.TextWrapper(width=max_characters, break_long_words=False)
    word_list = wrapper.wrap(text)
    if len(word_list) > max_height_text:
        word_list = word_list[:max_height_text]
        word_list.append("...")
    return word_list


def limit_overlap_text(overlap_list: list[str], max_lines: int = 3):
    if len(overlap_list) > max_lines:
        overlap_list = overlap_list[:max_lines]
    return overlap_list


def calc_font_size(ctx, string, face='Georgia', wanted_text_width=40, max_font_size: int = 10):
    ctx.save()
    font_size = 1
    # build up an appropriate font
    while True:
        ctx.select_font_face(face, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(font_size)
        # fascent, fdescent, fheight, fxadvance, fyadvance = ctx.font_extents()
        x_off, y_off, text_width, text_height, dx, dy = ctx.text_extents(string)
        if text_width < wanted_text_width and font_size < max_font_size:
            font_size += 1
        else:
            break
    return font_size


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


def create_svg(title_old: str, text_old: str, year_old: str, title_new: str, text_new: str, year_new: str,
               overlap_text: Union[str, list[str]], config: Config,
               output_path: Path, percentage_of_layers: float, max_width_text: int = 40,
               max_height_text: int = 4, to_bitmap: bool = False):
    """

    @param to_bitmap:
    @param title_old:
    @param text_old:
    @param year_old:
    @param title_new:
    @param text_new:
    @param year_new:
    @param overlap_text:
    @param config:
    @param output_path:
    @param percentage_of_layers:
    @param max_width_text:
    @param max_height_text:
    """
    surface = cairo.SVGSurface(str(output_path), config.sheet_width,
                               config.sheet_height)
    surface.set_document_unit(cairo.SVGUnit.MM)
    cr = cairo.Context(surface)
    # TEXT PARAMETERS & PLACEMENT VALUES
    cr.select_font_face("Sans",
                        cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_NORMAL)

    explanation = False  # explanation adds more descriptive text
    angle = percentage_of_layers * 2 * config.angle_offset - config.angle_offset  # function to make diagonal "move" throughout time
    radius = (config.sheet_width / 2 - config.offset_x_text) * 0.6
    cr.set_line_width(0.1)

    # --------background color for development---------
    # cr.set_source_rgb(100.0, 0.0, 0.0)
    # cr.rectangle(0, 0, config.sheet_width, config.sheet_height)
    # cr.fill()
    # --------rectangle for paper positioning---------
    cr.set_source_rgb(0.0, 0.0, 0.0)
    cr.rectangle(0, 0, config.sheet_width, config.sheet_height)
    cr.stroke()
    # -----------------OLD TEXT -----------------------
    cr.set_source_rgb(0, 0, 0)
    if explanation:
        # adapt the width of the text
        text_old = wrap_text_if_needed(cr, text_old, max_width_text, max_height_text)
        # Draw text
        for idx, i in enumerate(text_old):
            font_sz = calc_font_size(cr, i, face=config.fontface, wanted_text_width=config.extra_text_width,
                                     max_font_size=config.max_extra_fontsize)
            text(cr, i, (config.offset_x_text - idx * config.font_size, config.sheet_height / 2), angle=90,
                 font_size=font_sz, face=config.fontface)
    # -----------------OLD TITLE -----------------------
    font_sz = calc_font_size(cr, title_old, face=config.fontface, wanted_text_width=config.title_text_width,
                             max_font_size=config.max_title_fontsize)
    text(cr, title_old, (config.offset_x_title, config.sheet_height / 2), angle=90, font_size=font_sz,
         face=config.fontface)
    # # -----------------NEW TEXT-----------------------
    if explanation:
        # adapt the width of the text
        text_new = wrap_text_if_needed(cr, text_new, max_width_text, max_height_text)
        # Draw text
        for idx, i in enumerate(text_new):
            font_sz = calc_font_size(cr, i, face=config.fontface, wanted_text_width=config.extra_text_width,
                                     max_font_size=config.max_extra_fontsize)
            text(cr, i, (config.sheet_width - config.offset_x_text + idx * config.font_size, config.sheet_height / 2),
                 angle=270,
                 font_size=font_sz, face=config.fontface)
    # -----------------NEW TITLE-----------------------
    font_sz = calc_font_size(cr, title_new, face=config.fontface, wanted_text_width=config.title_text_width,
                             max_font_size=config.max_title_fontsize)
    text(cr, title_new, (config.sheet_width - config.offset_x_title, config.sheet_height / 2), angle=270,
         font_size=font_sz, face=config.fontface)
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
    overlap_text = limit_overlap_text(overlap_text, config.max_lines_circle)
    for idx, i in enumerate(overlap_text):
        # cr.set_font_size(config.max_circle_fontsize)
        # _text = wrap_text_if_needed(cr, i, 40, 1)
        font_sz = calc_font_size(cr, i, face=config.fontface, wanted_text_width=config.circle_text_width,
                                 max_font_size=config.max_circle_fontsize)
        if config.max_lines_circle == 1:
            text(cr, i,
                 (config.sheet_width / 2,
                  config.sheet_height / 2 - font_sz / 4),
                 0,
                 font_size=font_sz, face=config.fontface)
        else:
            text(cr, i,
                 (config.sheet_width / 2,
                  config.sheet_height / 2
                  - (len(overlap_text) - 1) / 2.0 * font_sz * 1.1 + idx * font_sz * 1.1),
                 0,
                 font_size=font_sz, face=config.fontface)
    # place the years on the circle as well
    print(angle)
    cr.set_font_size(config.year_fontsize)
    text_arc_path(cr, config.sheet_width / 2.0, config.sheet_height / 2.0, year_old, radius + 1.5,
                  np.radians(90 - angle))
    cr.fill()
    text_arc_path(cr, config.sheet_width / 2.0, config.sheet_height / 2.0, year_new, radius + 1.5,
                  np.radians(270 - angle))  # np.radians(270 + angle))
    cr.fill()
    if to_bitmap:
        surface.write_to_png("{}.png".format(os.path.splitext(output_path)[0]))


def adapt_svg_for_print(d):
    # TODO nog nodig??
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
    create_svg("lange titel", "vorige wc-rol met veel meer tekst dan de lijn toelaat", "2000", "titel",
               "volgende wc-rol",
               "2001",
               ["wc-rol", "grote test", "3"], config=config, output_path=Path("test_output_cairo.svg"),
               percentage_of_layers=0.4, max_width_text=100, max_height_text=1, to_bitmap=False)
