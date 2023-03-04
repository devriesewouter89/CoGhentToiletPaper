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
    draw_hatch: bool = True
    hatch_size: int = 16
    contour_simplify: int = 2
    no_polylines: bool = True
    resize: bool = True
    resolution: int = 1024


    # toilet paper sheet settings
    sheet_width = 110  # [mm]
    sheet_height = 80  # [mm]
    font_size = 5
    circle_fontsize = 6
    year_fontsize = 5

    # plot settings
    pen_pos_up = 26  # [0-100]
    pen_pos_down = 22  # [0-100]
    speed_pendown = 20  # [1-110]
    model = 4  # AxiDraw MiniKit
    reordering = 2  # optimize plot before plotting:  Full; Also allow path reversal

    # physical connections
    suction_GPIO = 18  # BCM


    # camera settings
    region_of_interest = (341, 7, 106, 346)