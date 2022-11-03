import ast
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from imageConversion.in_between_paper.in_between_generator import replace_text_in_svg
from imageConversion.linedraw.linedraw import LineDraw


def download_images_from_tree(csv_path: Path, output_path: Path):
    """

    @param csv_path:
    @param output_path:
    """
    df = pd.read_csv(str(csv_path))
    df = df.loc[(df["chosen"])]
    for index, row in df.iterrows():
        # print(index, row)
        print(row["img_uri"])
        img_data = requests.get(row["img_uri"]).content
        output_path.mkdir(parents=True, exist_ok=True)
        with open(Path(output_path / '{}.jpg'.format(int(row["layer"]))), 'wb') as handler:
            handler.write(img_data)


def convert_folder_to_linedraw(input_path: Path, output_path: Path, draw_contour: bool = True, draw_hatch: bool = True,
                               hatch_size: int = 16, contour_simplify: int = 2, resolution: int = 1024):
    """

    @param input_path:
    @param output_path:
    @param draw_contour:
    @param draw_hatch:
    @param hatch_size:
    @param contour_simplify:
    @param resolution:
    """
    ld = LineDraw(draw_contours=draw_contour, draw_hatch=draw_hatch, hatch_size=hatch_size,
                  contour_simplify=contour_simplify, resolution=resolution)
    for img in input_path.iterdir():
        output = Path(output_path / "{}.svg".format(os.path.splitext(img)[0]))
        ld.export_path = output
        input_img = Path(input_path / img)
        ld.sketch(str(input_img))


def create_in_between_images(csv_path: Path, output_path: Path, template_svg: Path):
    """

    @param csv_path:
    @param output_path:
    """
    # svg_path, text_1, text_2, output_path)
    df = pd.read_csv(str(csv_path), index_col=0)
    df = df.loc[(df["chosen"])]
    print(df.shape)
    for index, row in df.iterrows():
        # replace_text_in_svg(template_svg, )
        if index == 0:
            continue
        overlap = row["overlap"]
        res = ast.literal_eval(overlap)
        print(res)
        if type(res) == list():
            for overlap_element in res:
                if overlap_element.get("column") == "description":
                    overlap_text = overlap_element.get("overlap")
                    old_image_descr = overlap_element.get("text_orig")
                    new_image_descr = overlap_element.get("text_target")
                    # for key, val in overlap_element.items():
                    #     print(key, val)
        else:
            layer = row["layer"]
            overlap_text = res.get("overlap")
            old_image_descr = res.get("text_orig")
            new_image_descr = res.get("text_target")
        layer = row["layer"]
        old_image_year = int(row.get("origin_year"))
        new_image_year = int(row.get("target_year"))
        replace_text_in_svg(template_svg, text_old=old_image_descr, year_old=old_image_year, text_new=new_image_descr, year_new=new_image_year, output_path=Path(output_path / "{}".format(layer)),  max_len_text=30)

def resize_svgs_from_folder():
    print("todo based on svgelements")


if __name__ == '__main__':
    print(Path.cwd())
    parent = Path.cwd().parent
    in_between_out = Path(Path.cwd() / "images" / "in_between")
    in_between_out.mkdir(parents=True, exist_ok=True)
    # download_images_from_tree(csv_path=Path(parent / "dBPathFinder" / "DMG_tree.csv"),
    #                           output_path=Path(Path.cwd() / "images" / "input"))
    # convert_folder_to_linedraw(input_path=Path(Path.cwd() / "images" / "input"),
    #                            output_path=Path(Path.cwd() / "images" / "linedraw"))
    create_in_between_images(template_svg=Path(Path.cwd() / "in_between_paper" / "template.svg"),
                             output_path=in_between_out,
                             csv_path=Path(parent / "dBPathFinder" / "dmg_tree.csv"))
