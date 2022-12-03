"""
python file to check two or more lines from a csv file

"""
import ast
import math
import os
import random
from contextlib import suppress
from datetime import date
from os.path import join, dirname
from pathlib import Path
from queue import Queue
from threading import Thread

import numpy as np
import pandas as pd
from anytree import Node
from anytree.exporter import DotExporter
from dotenv import load_dotenv
from supabase_py import client
from tabulate import tabulate

from dBPathFinder.scripts.stemmer import sentence_to_stems, start_WordListCorpusReader
from dBPathFinder.scripts.supabase_link import get_sb_data

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
        self.tree_csv = tree_csv
        self.list_cols = list_cols
        self.stemmer_cols = stemmer_cols
        self.clean_time_col = "creation_date"  # "converted_creation_date"
        self.steps = steps
        self.amount_of_valid = self.df[self.clean_time_col].count()
        self.distance_per_step = math.floor(self.amount_of_valid / self.steps)
        self.spread = spread
        # print("Initial reading of the data: {}".format(self.df.describe))
        self.end_date: int = date.today().year
        self.object_tree = []  # list()
        self.df_tree = pd.DataFrame(columns=["layer", "id", "overlap", "parent", "img_uri", "chosen",
                                             "has_already_been_chosen", "origin_year", "target_year"])

        self.df_tree = self.df_tree.astype({"chosen": bool, "has_already_been_chosen": bool,
                                            "origin_year": int, "target_year": int})

        self.start_date: int = 0  # start_date we want to retrieve from the clean_time_col
        self.start_object = None
        self.start_idx: int = 0
        self.next_date = 0
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
        origin = self.df_row(origin_idx)
        target = self.df_row(target_idx)
        origin_year = int(origin["creation_date"])  # "converted_creation_date"
        target_year = int(target["creation_date"])
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
            return overlap_found, overlap_list[0], img_uri, target_idx, origin_year, target_year  # we use overlap_list
        else:
            return overlap_found, overlap_list, img_uri, target_idx, origin_year, target_year

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
        # idx = self.df[self.clean_time_col].idxmin(skipna=True)
        row_o_items = self.df.iloc[:self.spread]
        # we pick a random starting point in row_0
        self.insert_match_list_to_df(row_o_items, None)

    def get_date_from_original_df(self, idx) -> int:
        return int(self.df.iloc[idx][self.clean_time_col])

    def return_indices_in_list_range(self, start_idx: int, idx_distance: int, idx_spread: int) -> (bool, list[int]):
        new_origin = start_idx + idx_distance
        new_time_range = [new_origin - idx_spread,
                          new_origin + idx_spread]
        # valid except for border values
        if new_time_range[0] < 0:
            new_time_range[0] = 0
        if new_time_range[1] > len(self.df):
            new_time_range[1] = len(self.df)
        idx_list = self.df.index[new_time_range[0]:new_time_range[1]]
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
        res_df = pd.DataFrame(columns=["id", "overlap", "img_uri", "origin_year", "target_year"])
        for i in indexes:
            if i == origin:
                continue
            t = Thread(target=lambda q, arg1, arg2: q.put(self.find_overlap(arg1, arg2)), args=(que, origin, i))
            t.start()
            threads_list.append(t)
        for t in threads_list:
            t.join()
        while not que.empty():
            overlap_found, overlap_list, img_uri, index, origin_year, target_year = que.get()
            if overlap_found:
                # print(Fore.GREEN + "index: {}, origin: {}, overlap: {}".format(index, origin,  overlap_list) +
                # Style.RESET_ALL)
                temp_df = pd.DataFrame([[index, overlap_list, img_uri, origin_year, target_year]],
                                       columns=["id", "overlap", "img_uri", "origin_year", "target_year"])
                res_df = pd.concat([res_df, temp_df])
                res_found = True
            else:
                # print(Fore.RED + "no textual match found" + Style.RESET_ALL)
                continue
        return res_found, res_df
        # todo find per column the overlaps
        # todo return: boolean 'foundsmth', which indexes with which parameters: multiple options possible!

    def build_tree(self):
        print(tabulate(self.df_tree, headers='keys'))
        # Initialize the wordListcorpusreader object
        start_WordListCorpusReader()
        self.layer += 1  # we start searching for the next layer
        while self.layer < self.steps:
            chosen_in_previous_layer = self.df_tree[
                (self.df_tree["layer"] == self.layer - 1) & (self.df_tree['chosen'])]
            origin_idx = chosen_in_previous_layer["id"].values[0]
            rows_found, row_indices = self.return_indices_in_list_range(start_idx=origin_idx,
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
        return True

    def insert_match_list_to_df(self, item_list: pd.DataFrame | list[str], origin_idx: int | None):
        # pick a random starting point
        choose_idx = item_list["id"].sample(1).values[0]
        if self.layer == 0:
            # we know we're at the first line
            df_selection = item_list[["id", "img_uri"]].copy()
            df_selection["overlap"] = ""
            df_selection["origin_year"] = item_list["creation_date"]
            df_selection["target_year"] = item_list["creation_date"]
        else:
            df_selection = item_list[["id", "overlap", "img_uri", "origin_year", "target_year"]].copy()
        df_selection["parent"] = origin_idx  # None
        df_selection["layer"] = self.layer
        df_selection["chosen"] = False
        df_selection["has_already_been_chosen"] = False
        df_selection.loc[df_selection["id"] == choose_idx, "chosen"] = True
        df_selection.loc[df_selection["id"] == choose_idx, "has_already_been_chosen"] = True
        self.df_tree = pd.concat([df_selection, self.df_tree], ignore_index=True)
        self.df_tree.sort_values(by=["layer", "id"], inplace=True)
        self.df_tree.reset_index()
        return

    def forward_tree_build(self, row_indices, origin_idx):
        """
        @param row_indices: these are the indices in the original dataframe in which to look for matches
        @param origin_idx: this was the index in the original dataframe from the previous layer in the df_tree
        @return: True if successful, can be nested if no matches were immediately found!
        """
        if origin_idx in row_indices:
            print('found original object, removing it')
            row_indices = row_indices.delete(origin_idx)
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
            # print("we came at a dead-end by no matches found, return a layer and try another index")
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
        rand_idx = random.choice(other_rows.index.values)  # int(random.randrange(0, len(other_rows) - 1, 1))
        other_rows.at[rand_idx, "chosen"] = True
        other_rows.at[rand_idx, "has_already_been_chosen"] = True
        new_origin_idx = other_rows.at[rand_idx, "id"]
        self.df_tree.update(other_rows)
        print("went back, new origin: {}".format(new_origin_idx))
        return new_origin_idx

    def visualize_tree(self, depth: int):
        """
        Function that creates tree.png with in each layer the nodes written as "layer"_"identifier"
        @type depth: amount of layers we want to show (becomes easily very big)
        """
        # todo validate if this is correct by printing some links
        base_of_tree = self.df_tree[self.df_tree["layer"] == 0]["df_idx"].values[0]
        node_list = [[Node(name="{}_{}".format(0, base_of_tree))]]
        for layer in range(1, depth):
            idx_list = self.df_tree.loc[self.df_tree["layer"] == layer, "df_idx"].values.tolist()
            parent_list = self.df_tree.loc[self.df_tree["layer"] == layer, "parent"].values.astype(int).tolist()

            node_sub_list = []  # list()
            parent = None
            for i in range(len(idx_list)):
                for j in node_list[layer - 1]:
                    if int(j.name.split("_")[1]) == parent_list[i]:
                        parent = j
                node_sub_list.append(Node(name="{}_{}".format(layer, idx_list[i]), parent=parent))
            node_list_next = np.array(node_sub_list)
            node_list.append(node_list_next)
        DotExporter(node_list[0][0]).to_picture("tree.png")

    def save_tree(self):
        self.df_tree.to_csv(self.tree_csv, mode='a')

    def load_tree(self):
        self.df_tree = pd.read_csv(self.tree_csv)

    def print_tree(self):
        print(tabulate(self.df_tree, headers='keys'))


def find_tree(input_df, output_file, dataset, list_cols, stemmer_cols, amount_of_imgs_to_find):
    f_ol = FindOverlapOneBranch(df=input_df, tree_csv=output_file, list_cols=list_cols,
                                stemmer_cols=stemmer_cols,
                                steps=amount_of_imgs_to_find, spread=3, max_amount_of_threads=1000)
    # 3. we search for initial objects in a time-range from the first found object
    f_ol.build_tree()
    # fOL.print_tree()
    f_ol.visualize_tree(depth=50)


if __name__ == '__main__':
    dataset = "dmg"
    clean_file = Path(Path.cwd() / 'data' / "clean_data" / '{}.csv'.format(dataset))
    orig_file = Path(Path.cwd() / 'data' / '{}.csv'.format(dataset))
    # if clean_file.is_file():
    # input_file = clean_file
    # else:
    # input_file = orig_file
    list_cols = ['object_name', 'creator']
    stemmer_cols = ['title', 'description']
    amount_of_tissues = 100
    amount_of_imgs_to_find = math.floor(amount_of_tissues / 2)

    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)

    # warning, make sure your key is the secret key, not anon key if row level policy is enabled.
    URL = os.environ.get("URL")
    KEY = os.environ.get("KEY")
    sb = client.create_client(supabase_url=URL, supabase_key=KEY)
    input_df = get_sb_data(sb, dataset)

    input_df2 = pd.read_csv(clean_file)

    find_tree(input_df, "{}_tree.csv".format(dataset), dataset, list_cols, stemmer_cols, amount_of_imgs_to_find)
