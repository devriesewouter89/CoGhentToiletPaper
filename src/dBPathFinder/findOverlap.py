"""
python file to check two or more lines from a csv file

"""
import ast
import math
from contextlib import suppress
from datetime import date
from pathlib import Path
from queue import Queue
import random
from threading import Thread

import numpy as np
import pandas as pd
from anytree import Node
from anytree.exporter import DotExporter
from tabulate import tabulate
import sys
import os  # if you want this directory

try:
    sys.path.index(os.path.join(os.environ["HOME"], "CoGhentToiletPaper"))  # Or os.getcwd() for this directory
except ValueError:
    sys.path.append(os.path.join(os.environ["HOME"], "CoGhentToiletPaper"))  # Or os.getcwd() for this directory

from src.config_toilet import Config
from src.dBPathFinder.scripts.stemmer import sentence_to_stems, start_WordListCorpusReader
from src.dBPathFinder.scripts.supabase_link import get_sb_data, link_supabase
from typing import Union

"""
#todo write documentation


"""


class FindOverlapOneBranch:
    def __init__(self, df: pd.DataFrame, tree_csv,
                 list_cols: list[str], stemmer_cols: list[str], steps: int = 50, spread: int = 15,
                 max_amount_of_threads=10):
        """

        @type stemmer_cols: array of strings
        @type list_cols: array of strings
        """
        self.df = df
        self.output_fname = tree_csv
        self.list_cols = list_cols
        self.stemmer_cols = stemmer_cols
        self.clean_time_col = "creation_date"  # "converted_creation_date"
        self.steps = steps
        self.amount_of_valid = self.df[self.clean_time_col].count()
        self.distance_per_step = math.floor(self.amount_of_valid / self.steps)
        self.spread = spread
        # print("Initial reading of the data: {}".format(self.df.describe))
        self.end_date: int = date.today().year
        self.df_tree = pd.DataFrame(columns=["layer", "id", "overlap", "parent", "img_uri", "chosen",
                                             "has_already_been_chosen", "origin_year", "target_year", "origin_title",
                                             "target_title"])

        self.df_tree = self.df_tree.astype({"chosen": bool, "has_already_been_chosen": bool,
                                            "origin_year": int, "target_year": int})

        self.start_idx: int = 0
        self.layer = 0
        self.max_amount_of_threads = max_amount_of_threads
        # 1. let's set the starting point of our path
        self.find_first_entry()

    def find_overlap(self, origin_idx, target_idx) -> (bool, list[dict], str, int, int):
        """
        find_overlap is a function looking in a set of columns if overlapping text is to be found.
        @return:
        @param self:
        @param origin_idx: **index** of dataframe row where we'd like to find matches from
        @param target_idx: **index** dataframe row which we'll use to find matches with the origin
        @return: if an overlap is found, bool is set to True and a dict-list of overlapping strings
                and their originating column is returned
        """
        overlap_found = False
        overlap_list = list[dict]()
        # origin = self.df_row(origin_idx)
        try:
            origin = self.df.iloc[origin_idx, :]
            target = self.df.iloc[target_idx, :]
        except:
            print("something wrong")
            pass
        # target = self.df_row(target_idx)
        origin_year = int(origin["creation_date"])  # "converted_creation_date"
        target_year = int(target["creation_date"])
        origin_title = origin["title"]
        target_title = target["title"]
        for col in self.list_cols:
            # we need to unpack the strings to list via ast.literal_eval as otherwise we're evaluating character-based.
            # we use the try except statement as not always there are valid entries
            # try:
            with suppress(Exception):
                origin_entries = ast.literal_eval(origin[col])
                target_entries = ast.literal_eval(target[col])
                res = list(set(origin_entries).intersection(target_entries))
                if res:
                    overlap_found = True
                    overlap_list.append(
                        {"column": col, "overlap": res, "text_orig": origin[col], "text_target": target[col]})
            # except Exception as e:
            #     # print(e)
            #     pass
        for col in self.stemmer_cols:
            # try:
            with suppress(Exception):
                df1_res = sentence_to_stems(origin[col])
                df2_res = sentence_to_stems(target[col])
                res = list(set(df1_res).intersection(df2_res))
                if res:
                    overlap_found = True
                    overlap_list.append(
                        {"column": col, "overlap": res, "text_orig": origin[col], "text_target": target[col]})
            # except Exception as e:
            #     print(e)
            #     pass
        img_uri = target["img_uri"]

        if overlap_found:
            return overlap_found, overlap_list[
                0], img_uri, target_idx, origin_year, target_year, origin_title, target_title  # we use overlap_list
        else:
            return overlap_found, overlap_list, img_uri, target_idx, origin_year, target_year, origin_title, target_title

    def df_row(self, idx):
        """

        @param idx: index of row to access
        @return:
        """
        return self.df.iloc[idx, :]

    def find_first_entry(self):
        """
        finds the first elements in time recorded in the dataset
        sets the start_date as well as the initial object to get started with
        """
        # todo we expand this to have an array of possible starting points
        self.df = self.df.sort_values(by=self.clean_time_col)
        row_o_items = self.df.iloc[:self.spread]
        # we pick a random starting point in row_0
        self.insert_match_list_to_df(row_o_items, None)

    def get_date_from_original_df(self, idx) -> int:
        return int(self.df.iloc[idx][self.clean_time_col])

    def return_indices_in_list_range(self, start_idx: int, idx_distance: int, idx_spread: int) -> (bool, list[int]):
        """

        @param start_idx:
        @param idx_distance:
        @param idx_spread:
        @return:
        """
        new_origin = start_idx + idx_distance
        new_time_range = [new_origin - idx_spread,
                          new_origin + idx_spread]
        # valid except for border values
        if new_time_range[0] < 0:
            new_time_range[0] = 0
        if new_time_range[1] > len(self.df):
            new_time_range[1] = len(self.df)
        idx_list = self.df.index[new_time_range[0]:new_time_range[1]]
        if idx_list.empty:
            print("no indices found")
        return True, idx_list

    def find_overlap_threaded_in_series(self, origin, indexes) -> (bool, list[dict]):
        """
        @rtype: object
        @param origin: the index in the original dataframe for which we're looking for child in
                        <indexes> with a textual overlap
        @param indexes: the indexes of possible children
        """
        res_found = False

        # we'll multithread the find_overlap function to speed things up
        que = Queue()
        threads_list = []  # list()
        res_df = pd.DataFrame(
            columns=["id", "overlap", "img_uri", "origin_year", "target_year", "origin_title", "target_title"])
        for i in indexes:
            if i == origin:
                continue
            if np.isnan(origin):
                print("origin is nan")
            t = Thread(target=lambda q, arg1, arg2: q.put(self.find_overlap(arg1, arg2)), args=(que, origin, i))
            t.start()
            threads_list.append(t)
        for t in threads_list:
            t.join()
        while not que.empty():
            overlap_found, overlap_list, img_uri, index, origin_year, target_year, origin_title, target_title = que.get()
            if overlap_found:
                # print(Fore.GREEN + "index: {}, origin: {}, overlap: {}".format(index, origin,  overlap_list) +
                # Style.RESET_ALL)
                temp_df = pd.DataFrame(
                    [[index, overlap_list, img_uri, origin_year, target_year, origin_title, target_title]],
                    columns=["id", "overlap", "img_uri", "origin_year", "target_year", "origin_title", "target_title"])
                res_df = pd.concat([res_df, temp_df])
                res_found = True
            else:
                # print(Fore.RED + "no textual match found" + Style.RESET_ALL)
                continue
        res_df.set_index("id", inplace=True)
        return res_found, res_df

    def build_tree(self) -> pd.DataFrame:
        print(tabulate(self.df_tree, headers='keys'))
        # Initialize the wordListcorpusreader object
        start_WordListCorpusReader()
        self.layer += 1  # we start searching for the next layer
        while self.layer < self.steps:
            chosen_in_previous_layer = self.df_tree[
                (self.df_tree["layer"] == self.layer - 1) & (self.df_tree['chosen'])]
            origin_idx = int(chosen_in_previous_layer.index.values[0])  # ["id"].values[0]
            print(origin_idx)  # printing origin idx as sometimes its a nan
            if np.isnan(origin_idx):
                print("origin is nan")
            rows_found, row_indices = self.return_indices_in_list_range(start_idx=self.layer * self.distance_per_step,
                                                                        # origin_idx, todo changed this as otherwise
                                                                        #  I don't have control over when we'll reach
                                                                        #  the end point
                                                                        idx_distance=self.distance_per_step,
                                                                        idx_spread=self.spread)
            if rows_found:
                # 4. we remove the start index if present and check if we find semantic matches
                # FORWARD MOTION
                forward_build_success = self.forward_tree_build(row_indices=row_indices, origin_idx=origin_idx)
                if forward_build_success:
                    self.layer += 1
                else:
                    print("need to go to backward motion")
                    break
            else:

                print("we came at a dead end, there were no indices found in the timezone")
                print("end result:")
                print(tabulate(self.df_tree, headers='keys'))
                print('last date found: {}'.format(
                    self.get_date_from_original_df(
                        self.df_tree[self.df_tree["layer"] == self.layer - 1]["id"])))
                break
        self.save_tree()
        return self.df_tree

    def insert_match_list_to_df(self, item_list: pd.DataFrame, origin_idx: Union[int, None]):
        """
        this function takes a sub-selection of the entire dataframe, extracts the useful information
        and adds some columns for further processing
        @param item_list:
        @param origin_idx:
        @return:
        """
        # pick a random starting point
        # choose_idx = item_list["id"].sample(1).values[0]
        choose_idx = int(random.sample(item_list.index.values.tolist(), 1)[0])
        if self.layer == 0:
            # we know we're at the first line
            df_selection = item_list[["img_uri"]].copy()  # "id",
            df_selection["overlap"] = ""
            df_selection["origin_year"] = item_list["creation_date"]
            df_selection["target_year"] = item_list["creation_date"]
        else:
            df_selection = item_list[["overlap", "img_uri", "origin_year", "target_year"]].copy()  # "id",
            df_selection["origin_title"] = item_list["origin_title"]
            df_selection["target_title"] = item_list["target_title"]
        df_selection["parent"] = origin_idx  # None
        df_selection["layer"] = self.layer
        df_selection["chosen"] = False


        df_selection["has_already_been_chosen"] = False
        df_selection.loc[choose_idx, "chosen"] = True  # df_selection["id"] == choose_idx
        df_selection.loc[choose_idx, "has_already_been_chosen"] = True
        df_selection = df_selection.astype({"chosen": bool, "has_already_been_chosen": bool})
        self.df_tree = self.df_tree.astype({"chosen": bool, "has_already_been_chosen": bool})
        self.df_tree = pd.concat([df_selection, self.df_tree])  # , ignore_index=True)
        self.df_tree.sort_values(by=["layer"], inplace=True)  # , "id"
        # self.df_tree.reset_index()
        # self.df_tree.set_index('id', inplace=True)
        return

    def forward_tree_build(self, row_indices, origin_idx):
        """
        @param row_indices: these are the indices in the original dataframe in which to look for matches
        @param origin_idx: this was the index in the original dataframe from the previous layer in the df_tree
        @return: True if successful, can be nested if no matches were immediately found!
        """
        if origin_idx in row_indices:
            print('found original object, removing it')
            row_indices = list(row_indices).remove(origin_idx)
        if len(row_indices) < 1:
            print("no results")
            return False
        matches_found, matches = self.find_overlap_threaded_in_series(origin_idx, row_indices)
        if matches_found:
            print("{} matches found for layer {}".format(len(matches), self.layer))
            # we choose a random start option
            self.insert_match_list_to_df(matches, int(origin_idx))
            # print('matches had been found')
            return True
        else:
            print("we came at a dead-end by no matches found, return a layer and try another index")
            # print(tabulate(self.df_tree, headers='keys'))
            updated_origin_idx = self.backward_motion()
            if updated_origin_idx is None:
                return
            return self.forward_tree_build(row_indices, updated_origin_idx)

    def backward_motion(self):
        """
        backward motion steps up the ladder of our tree which we've created, as we've reached a dead end somewhere.
        In case we've tried all alternatives in a certain layer, we go up a layer extra and execture backward motion
        again.
        @return: we return the new index (of the original dataframe) of the new chosen path in the tree
        """
        # we return one layer to fetch a dead-end (self.next_layer - 1)
        # find the row where chosen was true and set it to false
        self.df_tree.loc[(self.df_tree["layer"] == (self.layer - 1)) & (self.df_tree["chosen"]), "chosen"] = False
        # choose a random other row and place it at true, as long as 'has_already_been_chosen' was false
        other_rows = self.df_tree.loc[
            (self.df_tree["layer"] == (self.layer - 1)) & (self.df_tree["chosen"] == False)
            & (self.df_tree["has_already_been_chosen"] == False)]
        if other_rows.empty:
            self.df_tree.drop(self.df_tree.loc[self.df_tree["layer"] == self.layer].index, inplace=True)
            if self.layer > 0:
                print("no more options in layer {}, we're going up one more".format(self.layer))
                # as long as we're not at the start again, we go back up a level
                self.layer -= 1
                return self.backward_motion()
            else:
                print("no more options in layer {}, we're expanding the spread".format(self.layer))
                # todo otherwise we'll widen the spread to start looking for matches
                # todo or we'll set a new starting point?
                self.spread += 2
                return None
            # todo: lower next_layer + remove df_tree entries which are belonging to next_layer
        # rand_idx = random.choice(other_rows.index.values)  # int(random.randrange(0, len(other_rows) - 1, 1))

        rand_idx = int(random.sample(other_rows.index.values.tolist(), 1)[0])
        other_rows.at[rand_idx, "chosen"] = True
        other_rows.at[rand_idx, "has_already_been_chosen"] = True
        new_origin_idx = rand_idx  # other_rows.loc[]#at[rand_idx, "id"]
        self.df_tree.update(other_rows)
        print("went back, new origin: {}".format(new_origin_idx))
        return new_origin_idx

    def visualize_tree(self, depth: int):
        """
        Function that creates tree.png with in each layer the nodes written as "layer"_"identifier"
        @type depth: amount of layers we want to show (becomes easily very big)
        #todo depth not correctly functioning?
        """
        node_list = []
        root = Node("root")
        try:
            for layer in range(0, depth):
                idx_list = self.df_tree.loc[self.df_tree["layer"] == layer].index.values.tolist()
                if layer > 0:
                    parent_list = self.df_tree.loc[self.df_tree["layer"] == layer, "parent"].values.astype(int).tolist()
                else:
                    parent_list = np.zeros((len(idx_list), 1))
                node_sub_list = []  # list()
                parent = None
                for i in range(len(idx_list)):
                    if layer > 0:
                        for j in node_list[layer - 1]:
                            if int(j.name.split("_")[1]) == parent_list[i]:
                                parent = j
                    else:
                        parent = root
                    used = self.df_tree.loc[
                        i]  # , not self.df_tree["chosen"] & self.df_tree["has_already_been_chosen"]]
                    color = "black"
                    if used.loc["chosen"]:
                        color = "green"
                    if (not used.loc["chosen"]) & (used.loc["has_already_been_chosen"]):
                        color = "red"
                    print(i, idx_list)
                    print(used)
                    node_sub_list.append(Node(name="{}_{}".format(layer, idx_list[i]), parent=parent, color=color))
                node_list_next = np.array(node_sub_list)
                node_list.append(node_list_next)
        except Exception as e:
            print(e)
            pass
        dot_exp = DotExporter(root, nodeattrfunc=self.set_color_shape)
        loc = os.path.splitext(self.output_fname)[0]
        dot_exp.to_picture("{}.png".format(loc))
        for line in dot_exp:
            print(line)

    def set_color_shape(self, node):
        """
        function to be able to set colors for our generated tree
        @return:
        """
        attrs = []
        attrs += [f'color={node.color}'] if hasattr(node, 'color') else []
        attrs += [f'shape={node.shape}'] if hasattr(node, 'shape') else []
        return ', '.join(attrs)

    def save_tree(self):
        self.df_tree.to_csv("{}".format(self.output_fname), mode='w')

    def load_tree(self):
        self.df_tree = pd.read_csv(self.output_fname)

    def print_tree(self):
        print(tabulate(self.df_tree, headers='keys'))


def find_tree(input_df: pd.DataFrame, output_file: Path, list_cols=None,
              stemmer_cols=None, amount_of_imgs_to_find: int = 50):
    """

    @param input_df: dataframe in which we want to find the path
    @type input_df: pd.Dataframe
    @param output_file: path (without an extension) to where we want to save the found path
    @type output_file: Path
    @param list_cols: columns which we want to check in the dataframe todo check if this is necessary
    @type list_cols: [str]
    @param stemmer_cols:columns which we want to check in the dataframe todo check if this is necessary
    @type stemmer_cols: [str]
    @param amount_of_imgs_to_find: half the amount of toilet paper sheets
    @type amount_of_imgs_to_find: int

    """
    if list_cols is None:
        list_cols = ['object_name', 'creator']
    if stemmer_cols is None:
        stemmer_cols = ['title', 'description']
    f_ol = FindOverlapOneBranch(df=input_df, tree_csv=output_file, list_cols=list_cols,
                                stemmer_cols=stemmer_cols,
                                steps=amount_of_imgs_to_find, spread=3, max_amount_of_threads=1000)
    # 3. we search for initial objects in a time-range from the first found object
    f_ol.build_tree()
    # fOL.print_tree()
    f_ol.visualize_tree(depth=50)


if __name__ == '__main__':
    config = Config()
    clean_file = config.clean_data_path

    # 1. Make connection with supabase database
    sb = link_supabase(config)
    # 2. fetch the dataframe for current location
    input_df = get_sb_data(sb, config.location)
    # 3. find a path in the data
    find_tree(input_df, config.tree_path, config.list_cols, config.stemmer_cols, config.amount_of_imgs_to_find)

    # input_df2 = pd.read_csv(clean_file)

# TODO something goes often wrong here, need to debug
# TODO bug in visualizing of tree, wrong parent gets chosen, colors are correct
# TODO sometimes we remove the old index and then things go wrong
