import ast
from pathlib import Path

import pandas as pd
import requests
import sys
import git
from pathlib import Path


def get_project_root():
    return Path(git.Repo('.', search_parent_directories=True).working_tree_dir)


try:
    sys.path.index(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
from config_toilet import Config

from config_toilet import Config
from imageConversion.in_between_paper.in_between_generator import create_svg
from linedraw.linedraw import LineDraw



def download_images_from_tree(df: pd.DataFrame, output_path: Path):
    """
    open the tree dataframe, find the chosen entries and download the belonging images
    @param df:
    @param output_path:
    """
    if df.chosen.dtypes.name == 'bool':
        df = df.loc[df['chosen']]
    else:
        df = df.loc[(df["chosen"] == 'True')]
    for index, row in df.iterrows():
        # print(index, row)
        print(row["img_uri"])
        img_data = requests.get(row["img_uri"]).content
        output_path.mkdir(parents=True, exist_ok=True)
        with open(Path(output_path / '{}.jpg'.format(int(row["layer"]))), 'wb') as handler:
            handler.write(img_data)


def convert_polyline_to_path(svg_file: Path):
    """
    the [saxi](https://github.com/nornagon/saxi) library is not capable of using polylines, due to dependency issue.
    A quick fix is to convert polylines to paths in svg
    @param svg_file: file to convert to use only paths and no polylines
    """
    with open(svg_file, 'r') as f:
        data = f.read()
    # replace polyline with path
    data = data.replace("polyline", "path")
    # replace points=" with d="M
    data = data.replace('points="', 'd="M')
    with open(svg_file, 'w') as file:
        file.write(data)


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
    output_path.mkdir(parents=True, exist_ok=True)
    for img in input_path.iterdir():
        output = Path(output_path / "{}.svg".format(img.stem))
        ld.export_path = output
        input_img = Path(input_path / img)
        ld.sketch(str(input_img))
        convert_polyline_to_path(output)


def create_in_between_images(df: pd.DataFrame, output_path: Path, config: Config):
    """

    @param config:
    @param df:
    @param output_path:
    """
    output_path.mkdir(parents=True, exist_ok=True)

    if df.chosen.dtypes.name == 'bool':
        df = df.loc[df['chosen']]
    else:
        df = df.loc[(df["chosen"] == 'True')]
    print(df.shape)
    df = df.reset_index()
    amount_of_layers = len(df)
    for index, row in df.iterrows():
        old_image_descr = None
        new_image_descr = None
        overlap_text = None
        if index == 0:
            continue
        overlap = row["overlap"]
        res = ast.literal_eval(overlap)
        if type(res) == list():
            for overlap_element in res:
                if overlap_element.get("column") == "description":
                    overlap_text = overlap_element.get("overlap")
                    old_image_descr = overlap_element.get("text_orig")
                    new_image_descr = overlap_element.get("text_target")
        else:
            overlap_text = res.get("overlap")
            old_image_descr = res.get("text_orig")
            new_image_descr = res.get("text_target")
        layer = row["layer"]
        old_image_year = int(row.get("origin_year"))
        new_image_year = int(row.get("target_year"))
        create_svg(title_old="", text_old=old_image_descr, year_old=str(old_image_year),
                   title_new="", text_new=new_image_descr, year_new=str(new_image_year),
                   overlap_text=overlap_text, percentage_of_layers=float(float(layer) / amount_of_layers),
                   output_path=Path(output_path / "{}.svg".format(layer)),
                   sheet_height=config.sheet_height,
                   sheet_width=config.sheet_width,
                   font_size=config.font_size)
        # replace_text_in_svg(template_svg, text_old=old_image_descr, year_old=old_image_year,
        # text_new=new_image_descr, year_new=new_image_year, output_path=Path(output_path / "{}".format(layer)),
        # max_len_text=30)


def resize_svgs_from_folder():
    print("todo based on svgelements")


if __name__ == '__main__':
    print(Path.cwd())
    parent = Path.cwd().parent
    csv_path = Path(parent / "dBPathFinder" / "dmg_tree.csv")
    df = pd.read_csv(str(csv_path), index_col=0)

    download_images_from_tree(df=df,
                              output_path=Path(Path.cwd() / "images" / "input"))
    convert_folder_to_linedraw(input_path=Path(Path.cwd() / "images" / "input"),
                               output_path=Path(Path.cwd() / "images" / "linedraw"))

    in_between_out = Path(Path.cwd() / "images" / "in_between")
    in_between_out.mkdir(parents=True, exist_ok=True)
    create_in_between_images(df=df, output_path=in_between_out)
