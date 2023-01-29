import math
import os
import sys
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
    ROOT_DIR = Path(get_git_root(Path.cwd())) #os.path.abspath(os.curdir)

    dotenv_path = Path(ROOT_DIR / ".env")
    load_dotenv(dotenv_path)
    # warning, make sure your key is the secret key, not anon key if row level policy is enabled.
    URL = os.environ.get("URL")
    KEY = os.environ.get("KEY")

    # timestamp: str = "2021-10-20T00:00:00.309Z"
    # context: str = "src/utils/context.jsonld"

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

    # toilet paper sheet settings
    sheet_width = 100 # [mm]
    sheet_height = 50 # [mm]
    font_size = 4
    circle_fontsize = 5
    year_fontsize = 4

    # plot settings
    pen_pos_up = 30 # [0-100]
    pen_pos_down = 20 # [0-100]
    speed_pendown = 20 # [1-110]
    model = 4 #  AxiDraw MiniKit
    reordering = 2 # optimize plot before plotting:  Full; Also allow path reversal
