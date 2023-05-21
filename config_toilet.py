import math
import os
from dataclasses import dataclass
from pathlib import Path

import git
from dotenv import load_dotenv


def get_git_root(path):
    git_repo = git.Repo(path, search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")
    return git_root


@dataclass
class Config:
    location = "dmg"
    ROOT_DIR = Path(get_git_root(Path.cwd()))  # os.path.abspath(os.curdir)

    dotenv_path = Path(ROOT_DIR / ".env")
    load_dotenv(dotenv_path)
    # warning, make sure your key is the secret key, not anon key if row level policy is enabled.
    URL = os.environ.get("URL")
    KEY = os.environ.get("KEY")

    location_files = Path(ROOT_DIR / "location_files" / location)

    # config settings for path finding
    raw_data_path = Path(location_files / "raw.csv")
    clean_data_path = Path(location_files / "clean.csv")
    tree_path = Path(location_files / "tree.csv")
    list_cols = ['object_name', 'creator']
    stemmer_cols = ['title', 'description']
    amount_of_tissues = 100
    amount_of_imgs_to_find = math.floor(amount_of_tissues / 2)

    # config settings for image conversions & creations
    tree_img_path = Path(location_files / "orig_imgs")
    converted_img_path = Path(location_files / "converted_imgs")
    in_between_page_path = Path(location_files / "in_between")
    draw_contour: bool = True
    draw_hatch: bool = False
    hatch_size: int = 16
    contour_simplify: int = 3
    no_polylines: bool = True
    resize: bool = True
    resolution: int = 1024
    fixed_size: bool = True

    # toilet paper sheet settings
    sheet_width = 110  # [mm]
    sheet_height = 80  # [mm]
    font_size = 4
    max_title_fontsize = 10
    max_circle_fontsize = 10
    max_extra_fontsize = 10
    year_fontsize = 10
    offset_x_text = 25
    offset_x_title = 15
    angle_offset = 20
    radius = (sheet_width / 2 - offset_x_text) * 0.6
    title_text_width = 40
    circle_text_width = 2 * radius - 4
    extra_text_width = 30
    fontface = 'sans'
    max_lines_circle = 2

    # plot settings
    pen_pos_up = 24  # [0-100]
    pen_pos_down = 13  # [0-100]
    speed_pendown = 20  # [1-110]
    model = 4  # AxiDraw MiniKit
    reordering = 2  # optimize plot before plotting:  Full; Also allow path reversal

    paper_offset = (0.1, 0.1) #TODO (x,y) coordinates where the paper is approx positioned

    # physical connections
    suction_GPIO = 18  # BCM
    stepperi2c = 0x63


    # camera settings
    region_of_interest = (280, 51, 30, 429)
    prep_img = Path(location_files / "prep.jpg")
    template = Path(location_files / "template.jpg")
    temp_img = Path(location_files / "temp.jpg")
