import math
import os
import sys
from dataclasses import dataclass


@dataclass
class Config:

    location = "stam"



    ROOT_DIR = os.path.abspath(os.curdir)

    # check which platform to define path structure.
    if sys.platform == "darwin" or sys.platform == "linux":
        data_path = os.path.join(ROOT_DIR, "data")
    else:
        data_path = ROOT_DIR + "data"  # used to be: \\src\\utils\\data

    timestamp: str = "2021-10-20T00:00:00.309Z"
    context: str = "src/utils/context.jsonld"

    location_files = os.path.join(ROOT_DIR, "location_files", location)

    # config settings for path finding
    clean_data_path = os.path.join(location_files, "{}.csv".format(location))
    tree_path = os.path.join(location_files, "{}_tree.csv".format(location))
    list_cols = ['object_name', 'creator']
    stemmer_cols = ['title', 'description']
    amount_of_tissues = 100
    amount_of_imgs_to_find = math.floor(amount_of_tissues / 2)
