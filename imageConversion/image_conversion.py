import os
from pathlib import Path

import pandas as pd
import requests

from imageConversion.linedraw.linedraw import LineDraw

from svgelements import *

def download_images_from_tree(csv_path: Path, output_path: Path):
    df = pd.read_csv(csv_path)
    df = df.loc[(df["chosen"])]
    for index, row in df.iterrows():
        # print(index, row)
        print(row["img_uri"])
        img_data = requests.get(row["img_uri"]).content
        with open(Path(output_path / '{}.jpg'.format(int(row["layer"]))), 'wb') as handler:
            handler.write(img_data)


def convert_folder_to_linedraw(input_path: Path, output_path: Path, draw_contour: bool = True, draw_hatch: bool = True,
                               hatch_size: int = 16, contour_simplify: int = 2, resolution: int = 1024):
    ld = LineDraw(draw_contours=draw_contour, draw_hatch=draw_hatch, hatch_size=hatch_size,
                           contour_simplify=contour_simplify, resolution=resolution)
    for img in os.listdir(input_path):
        output = Path(output_path / "{}.svg".format(os.path.splitext(img)[0]))
        ld.export_path = output
        input_img = os.path.join(input_path, img)
        ld.sketch(input_img)

def resize_svgs_from_folder():
    print("todo based on svgelements")

if __name__ == '__main__':
    print(Path.cwd())
    parent = Path.cwd().parent
    # download_images_from_tree(csv_path=Path(parent / "dBPathFinder" / "DMG_tree.csv"),
    #                           output_path=Path(Path.cwd() / "images" / "input"))
    convert_folder_to_linedraw(input_path=str(Path(Path.cwd() / "images" / "input")),
                               output_path=Path(Path.cwd() / "images" / "linedraw"))
