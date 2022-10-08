"""
python file to check two or more lines from a csv file

"""
import ast
import math
import os
import random
import time
from contextlib import suppress
from datetime import date
from pathlib import Path
from queue import Queue
from threading import Thread

import numpy as np
import pandas as pd
from anytree import Node
from anytree.exporter import DotExporter
from colorama import Fore, Style
from tabulate import tabulate

from preprocess_df import PrepDf, chunker
from stemmer import sentence_to_stems, start_WordListCorpusReader


class FindOverlapOneBranch:
    def __init__(self, df, tree_csv, list_cols: list[str], stemmer_cols: list[str], steps: int = 50, spread: int = 15,
                 max_amount_of_threads=10):
        """

        @type stemmer_cols: array of strings
        @type list_cols: array of strings
        """
        self.df = df
        self.tree_csv = tree_csv
        self.list_cols = list_cols
        self.stemmer_cols = stemmer_cols
        self.clean_time_col = "converted_creation_date"
        self.steps = steps
        self.amount_of_valid = self.df[self.clean_time_col].count()
        self.distance_per_step = math.floor(self.amount_of_valid / self.steps)
        self.spread = spread
        # print("Initial reading of the data: {}".format(self.df.describe))
        self.end_date: int = date.today().year
        self.object_tree = []  # list()
        self.df_tree = pd.DataFrame(columns=["layer", "df_idx", "overlap", "parent", "img_uri", "chosen",
                                             "has_already_been_chosen"])

        self.df_tree = self.df_tree.astype({"chosen": bool, "has_already_been_chosen": bool})

        self.start_date: int = 0  # start_date we want to retrieve from the clean_time_col
        self.start_object = None
        self.start_idx: int = 0
        self.next_date = 0
        self.next_layer = 1
        self.max_amount_of_threads = max_amount_of_threads
        # 1. let's set the starting point of our path
        self.find_first_entry()

    def find_overlap(self, origin_idx, target_idx) -> (bool, list[dict], str):
        """
        find_overlap is a function looking in a set of columns if overlapping text is to be found.
        @param self:
        @param origin_idx: **index** of dataframe row where we'd like to find matches from
        @param target_idx: **index** dataframe row which we'll use to find matches with the origin
        @return: if an overlap is found, bool is set to True and a dict-list of overlapping strings and their originating column is returned
        """
        overlap_found = False
        overlap_list = list[dict]()
        origin = self.df_row(origin_idx)
        target = self.df_row(target_idx)

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
        return overlap_found, overlap_list, img_uri, target_idx

    def df_row(self, idx):
        """

        @param idx: index of row to access
        @return:
        """
        return self.df.iloc[idx, :]

    def find_first_entry(self):
        """
        finds the first element in time recorded in the dataset
        sets the start_date as well as the initial object to get started with
        """
        idx = self.df[self.clean_time_col].idxmin(skipna=True)
        self.start_idx = idx
        self.start_object = self.df.iloc[idx]
        self.start_date = self.df.iloc[idx][self.clean_time_col]
        img_uri = self.df.iloc[idx]["img_uri"]
        self.df_tree = pd.concat([self.df_tree, pd.DataFrame.from_records(
            [{"layer": 0, "df_idx": self.start_idx, "overlap": "", "parent": None, "img_uri": img_uri, "chosen": True,
        "has_already_been_chosen": True}])])

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

    def find_overlap_threaded_in_series(self, origin, indexes) -> (bool, list[dict], list[str]):
        """
        @rtype: object
        @param origin: the index in the original dataframe for which we're looking for childs in <indexes> with a textual overlap
        @param indexes: the indexes of possible children
        """

        # print("origin:")
        # print(self.df_row(origin))
        res = []  # list()
        res_found = False

        # we'll multithread the find_overlap function to speed things up
        que = Queue()
        threads_list = []  # list()
        for i in indexes:
            if i == origin:
                continue
            t = Thread(target=lambda q, arg1, arg2: q.put(self.find_overlap(arg1, arg2)), args=(que, origin, i))
            t.start()
            threads_list.append(t)
        for t in threads_list:
            t.join()
        while not que.empty():
            overlap_found, overlap_list, img_uri, index = que.get()
            if overlap_found:
                # print(Fore.GREEN + "index: {}, origin: {}, overlap: {}".format(index, origin,  overlap_list) + Style.RESET_ALL)
                res.append({"index": index, "overlap": overlap_list, "img_uri": img_uri})
                res_found = True
            else:
                # print(Fore.RED + "no textual match found" + Style.RESET_ALL)
                continue
        return res_found, res
        # todo find per column the overlaps
        # todo return: boolean 'foundsmth', which indexes with which parameters: multiple options possible!

    def build_tree(self):
        print(tabulate(self.df_tree, headers='keys'))
        # Initialize the wordListcorpusreader object
        start_WordListCorpusReader()

        while self.next_layer < self.steps:
            chosen_in_previous_layer = self.df_tree[
                (self.df_tree["layer"] == self.next_layer - 1) & (self.df_tree['chosen'])]
            origin_idx = chosen_in_previous_layer["df_idx"].values[0]
            rows_found, row_indices = self.return_indices_in_list_range(start_idx=origin_idx,
                                                                        idx_distance=self.distance_per_step,
                                                                        idx_spread=self.spread)
            if rows_found:
                # 4. we remove the start index if present and check if we find semantic matches
                # FORWARD MOTION
                forward_build_success = self.forward_tree_build(row_indices=row_indices, origin_idx=origin_idx)
                if forward_build_success:
                    self.next_layer += 1
                else:
                    print("need to go to backward motion")
                    break
            else:
                print("we came at a dead end, there were no indices found in the timezone")
                print("end result:")
                print(tabulate(self.df_tree, headers='keys'))
                print('last date found: {}'.format(
                    self.get_date_from_original_df(
                        self.df_tree[self.df_tree["layer"] == self.next_layer - 1]["df_idx"])))
                break
        self.save_tree()

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
            print("{} matches found for layer {}".format(len(matches), self.next_layer))
            # we choose a random start option
            choose_idx = random.randint(0, len(matches) - 1)
            for idx, i in enumerate(matches):
                if idx == choose_idx:
                    choose_this = True
                else:
                    choose_this = False
                df_idx = i["index"]
                prev_match = i["overlap"]
                img_uri = i["img_uri"]
                temp = pd.DataFrame.from_records(
                    [{"layer": self.next_layer, "df_idx": df_idx, "overlap": prev_match, "img_uri": img_uri,
                      "chosen": choose_this, "has_already_been_chosen": choose_this, "parent": int(origin_idx)}])
                temp = temp.astype({"chosen": bool, "has_already_been_chosen": bool})
                self.df_tree = pd.concat([self.df_tree, temp],
                                         ignore_index=True)
            # print('matches had been found')
            # self.df_tree.reset_index()
            return True
        else:
            # print("we came at a dead-end by no matches found, return a layer and try another index")
            # print(tabulate(self.df_tree, headers='keys'))
            # return False  # todo call backward motion
            updated_origin_idx = self.backward_motion()
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
        self.df_tree.loc[(self.df_tree["layer"] == (self.next_layer - 1)) & (self.df_tree["chosen"]), "chosen"] = False
        # choose a random other row and place it at true, as long as 'has_already_been_chosen' was false
        other_rows = self.df_tree.loc[
            (self.df_tree["layer"] == (self.next_layer - 1)) & (self.df_tree["chosen"] == False)
            & (self.df_tree["has_already_been_chosen"] == False)]
        if other_rows.empty:
            print("no more options in layer {}, we're going up one more".format(self.next_layer))
            self.df_tree.drop(self.df_tree.loc[self.df_tree["layer"] == self.next_layer].index, inplace=True)
            self.next_layer -= 1
            # todo: lower next_layer + remove df_tree entries which are belonging to next_layer
            return self.backward_motion()
        rand_idx = random.choice(other_rows.index.values)  # int(random.randrange(0, len(other_rows) - 1, 1))
        other_rows.at[rand_idx, "chosen"] = True
        other_rows.at[rand_idx, "has_already_been_chosen"] = True
        new_origin_idx = other_rows.at[rand_idx, "df_idx"]
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


if __name__ == '__main__':
    dataset = "STAM"
    clean_file = Path(Path.cwd() / 'LDES_TO_PG' / 'data' / "clean_data"/ '{}.csv'.format(dataset))
    orig_file = Path(Path.cwd() / 'LDES_TO_PG' / 'data' / '{}.csv'.format(dataset))
    if clean_file.is_file():
        input_file = clean_file
    else:
        input_file = orig_file
    list_cols = ['object_name', 'creator']
    stemmer_cols = ['title', 'description']
    amount_of_tissues = 100
    amount_of_imgs_to_find = math.floor(amount_of_tissues / 2)

    # 1. we make a pandas dataframe for manipulation
    clean_df = PrepDf(input_csv=input_file, clean_csv=clean_file, institute= dataset, time_col= "creation_date", steps=amount_of_imgs_to_find)

    # 2. to get some insights in the distribution of the data: enable next statement
    clean_df.plot_distribution()
    #
    fOL = FindOverlapOneBranch(df=clean_df.df, tree_csv="{}_tree.csv".format(dataset), list_cols=list_cols,
                               stemmer_cols=stemmer_cols,
                               steps=amount_of_imgs_to_find, spread=3, max_amount_of_threads=1000)
    # 3. we search for initial objects in a time-range from the first found object
    fOL.build_tree()
    # fOL.print_tree()
    # fOL.save_tree()
    # print("saved tree")
    # fOL.load_tree()
    fOL.visualize_tree(depth=50)
    # fOL.get_image_list_from_tree()

    # index_list = fOL.df_tree[fOL.df_tree["chosen"] == True].index
    # for i in index_list:
    #     print(fOL.get_image_uri(fOL.get_object_id(i)))
