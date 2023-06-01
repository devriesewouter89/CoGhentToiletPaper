import ast
import sys
from pathlib import Path

import git
import pandas as pd
import requests
from linedraw.linedraw import LineDraw
from imageConversion.in_between_paper.in_between_generator import create_svg


def get_project_root():
    return Path(git.Repo('.', search_parent_directories=True).working_tree_dir)


try:
    sys.path.index(str(get_project_root().resolve()))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(str(get_project_root().resolve()))  # Or os.getcwd() for this directory

from config_toilet import Config


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


def convert_folder_to_linedraw(input_path: Path, output_path: Path, config: Config):
    """

    @param input_path:
    @param output_path:
    @param draw_contour:`
    @param draw_hatch:
    @param hatch_size:
    @param contour_simplify:
    @param resolution:
    """
    ld = LineDraw(draw_contours=config.draw_contour, draw_hatch=config.draw_hatch, hatch_size=config.hatch_size,
                  contour_simplify=config.contour_simplify, no_polylines=config.no_polylines, resize=config.resize,
                  longest=config.sheet_width, shortest=config.sheet_height, resolution=config.resolution,
                  draw_border=True, offset=config.paper_offset, fixed_size=config.fixed_size)
    output_path.mkdir(parents=True, exist_ok=True)
    for img in input_path.iterdir():
        output = Path(output_path / "{}.svg".format(img.stem))
        ld.export_path = output
        input_img = Path(input_path / img)
        ld.sketch(str(input_img))


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
        old_title = row.get("origin_title")
        new_title = row.get("target_title")
        create_svg(title_old=old_title, text_old=old_image_descr, year_old=str(old_image_year),
                   title_new=new_title, text_new=new_image_descr, year_new=str(new_image_year),
                   overlap_text=overlap_text, percentage_of_layers=float(float(layer) / amount_of_layers),
                   output_path=Path(output_path / "{}.svg".format(layer)),
                   config=config, to_bitmap=False)
        # replace_text_in_svg(template_svg, text_old=old_image_descr, year_old=old_image_year,
        # text_new=new_image_descr, year_new=new_image_year, output_path=Path(output_path / "{}".format(layer)),
        # max_len_text=30)


if __name__ == '__main__':
    print(Path.cwd())
    config = Config()
    csv_path = config.tree_path
    df = pd.read_csv(str(csv_path), index_col=0)

    download_images_from_tree(df=df,
                              output_path=config.tree_img_path)
    convert_folder_to_linedraw(input_path=config.tree_img_path,
                               output_path=config.converted_img_path, config=config)

    create_in_between_images(df=df, output_path=config.in_between_page_path, config=config)
