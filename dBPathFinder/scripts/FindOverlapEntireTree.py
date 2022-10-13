import ast
import math
from contextlib import suppress
from datetime import time, date
from lib2to3.pytree import Node
from queue import Queue
from threading import Thread

import numpy as np
import pandas as pd
from anytree.exporter import DotExporter
from colorama import Fore, Style
from tabulate import tabulate

from dBPathFinder.preprocess_df import chunker
from dBPathFinder.stemmer import sentence_to_stems, start_WordListCorpusReader


class FindOverlapEntireTree:
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
        self.df_tree = pd.DataFrame(columns=["layer", "df_idx", "overlap", "parent", "img_uri"])  # "chosen",
        # "has_already_been_chosen"])
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
        self.df_tree = pd.concat([self.df_tree, pd.DataFrame.from_records(
            [{"layer": 0, "df_idx": self.start_idx, "previous_match": "", "parent": None}])])  # "chosen": True,
        # "has_already_been_chosen": True}])])

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

    def forward_tree_build_no_child_chosen(self, row_indices, origin_idx) -> pd.DataFrame:
        """
        @param row_indices: these are the indices in the original dataframe in which to look for matches
        @param origin_idx: this was the index in the original dataframe from the previous layer in the df_tree
        @return: True if successful, can be nested if no matches were immediately found!
        """
        df_temp = pd.DataFrame()

        if origin_idx in row_indices:
            print('found original object, removing it')
            row_indices = row_indices.delete(origin_idx)
        if len(row_indices) < 1:
            print("no results")
            return df_temp  # todo return value necessary?
        matches_found, matches = self.find_overlap_threaded_in_series(origin_idx, row_indices)
        if matches_found:
            for idx, i in enumerate(matches):
                df_idx = i["index"]
                img_uri = i["img_uri"]
                overlap = i["overlap"]
                df_temp = pd.concat([df_temp, pd.DataFrame.from_records(
                    [{"layer": self.next_layer, "df_idx": df_idx, "overlap": overlap, "img_uri": img_uri,
                      "parent": int(origin_idx)}])], ignore_index=True)
        # else:
        #     print("No matches found")
        return df_temp  # todo return value necessary?

    def forward_build_thread(self, origin_idx):
        rows_found, row_indices = self.return_indices_in_list_range(start_idx=origin_idx,
                                                                    idx_distance=self.distance_per_step,
                                                                    idx_spread=self.spread)
        if rows_found:
            df_temp = self.forward_tree_build_no_child_chosen(row_indices=row_indices,
                                                              origin_idx=origin_idx)
            return df_temp
        # else:
        #     return

    def build_tree(self):
        print(tabulate(self.df_tree, headers='keys'))
        # Initialize the wordListcorpusreader object
        start_WordListCorpusReader()
        queue = Queue()
        while self.next_layer < self.steps:
            print("===> upping to layer {}".format(self.next_layer))
            # we look for the "new" to become parents: Pandas Series
            chosen_in_previous_layer = self.df_tree[
                (self.df_tree["layer"] == self.next_layer - 1)]
            origin_idx_list = chosen_in_previous_layer["df_idx"].values
            print("amount of ids to check: {}".format(len(origin_idx_list)))
            for pos, chunk in chunker(origin_idx_list, self.max_amount_of_threads):
                thread_list_parent = []  # list()

                for origin_idx in chunk:
                    t = Thread(target=lambda q, arg1: q.put(self.forward_build_thread(arg1)), args=(queue, origin_idx))
                    # t = Thread(target=self.forward_build_thread, args=[queue, origin_idx])
                    thread_list_parent.append(t)
                _time = time.strftime("%H:%M:%S", time.localtime())
                print(
                    Fore.CYAN + "amount of threads to be started is: {} at pos {}. {} total threads this layer".format(
                        len(chunk * self.spread * 2),
                        pos,
                        len(thread_list_parent)) + Style.RESET_ALL
                )
                print("time is {}".format(_time))
                for i in thread_list_parent:
                    i.start()
                for i in thread_list_parent:
                    i.join(timeout=120.0)
                    if i.is_alive():
                        print("=============thread {} has timed out================".format(i))
                while not queue.empty():
                    df_temp = queue.get()
                    self.df_tree = pd.concat([self.df_tree, df_temp], ignore_index=True)
            self.save_tree()

            # self.forward_build_thread(origin_idx)
            self.next_layer += 1
        # todo now we need a function to find the path

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

