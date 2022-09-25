'''
python file to check two or more lines from a csv file

'''
import ast
import json
import math
import multiprocessing
import os
import random
import time
import urllib
from datetime import date
from multiprocessing import Process
from threading import Thread
from queue import Queue
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import numpy as np
import pandas as pd
from anytree.exporter import DotExporter
from colorama import Fore, Style
from matplotlib import pyplot as plt
from tabulate import tabulate

from stemmer import sentence_to_stems, start_WordListCorpusReader
from anytree import Node, RenderTree


def chunker(seq, size):
    """
    function to iterate over lists in chunks, useful for massive threadlists
    @param seq:
    @param size:
    @return:
    """
    return ((pos, seq[pos:pos + size]) for pos in range(0, len(seq), size))


class FindOverlap:
    def __init__(self, file, institute: str, time_col: str, list_cols: list[str], stemmer_cols: list[str], steps: int):
        """

        @type stemmer_cols: array of strings
        @type list_cols: array of strings
        """
        self.file = file
        self.time_col = time_col
        self.institute = institute
        self.clean_time_col = "converted_creation_date"
        self.list_cols = list_cols
        self.stemmer_cols = stemmer_cols
        self.df = pd.read_csv(file).drop_duplicates()
        # print("Initial reading of the data: {}".format(self.df.describe))
        self.end_date: int = date.today().year
        self.steps = steps
        self.object_tree = list()
        self.df_tree = pd.DataFrame(columns=["layer", "df_idx", "previous_match", "parent", "img_uri"])  # "chosen",
        # "has_already_been_chosen"])
        self.start_date: int = 0  # start_date we want to retrieve from the clean_time_col
        self.start_object = None
        self.start_idx: int = 0
        self.next_date = 0
        self.next_layer = 1
        # 1. the dates are not easily human-readable, let's convert them
        self.convert_column_first_year_via_regex()
        self.amount_of_valid = self.df[self.clean_time_col].count()
        self.amount_of_nan = self.df[self.clean_time_col].isna().sum()
        self.distance_per_step = math.floor(self.amount_of_valid / self.steps)
        self.spread = 30
        # 2. sort the dataframe and drop the elements which have no clear date
        self.sort_and_drop_na_df()
        # 3. let's set the starting point of our path
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
        # First we test if the target_idx has an image, otherwise it's useless
        _, img_uri = self.get_image_uri(self.get_object_id(target_idx))
        if img_uri is None:
            # we return an empty list as we haven't got an image.
            return overlap_found, overlap_list, img_uri, None

        for col in self.list_cols:
            # we need to unpack the strings to list via ast.literal_eval as otherwise we're evaluating character-based.
            # we use the try except statement as not always there are valid entries
            try:
                origin_entries = ast.literal_eval(origin[col])
                target_entries = ast.literal_eval(target[col])
                res = list(set(origin_entries).intersection(target_entries))
                if res:
                    overlap_found = True
                    overlap_list.append({"column": col, "overlap": res})
            except Exception as e:
                # print(e)
                pass
        for col in self.stemmer_cols:
            try:
                df1_res = sentence_to_stems(origin[col])
                df2_res = sentence_to_stems(target[col])
                res = list(set(df1_res).intersection(df2_res))
                if res:
                    overlap_found = True
                    overlap_list.append({"column": col, "overlap": res})
            except Exception as e:
                print(e)
                pass
        return overlap_found, overlap_list, img_uri, target_idx

    def df_row(self, idx):
        """

        @param idx: index of row to access
        @return:
        """
        return self.df.iloc[idx, :]

    def find_indices_in_time_range(self, origin_year: int, time_distance: int, time_spread: int) -> (bool, list[int]):
        new_origin = origin_year + time_distance
        new_time_range = [new_origin - time_spread,
                          new_origin + time_spread]
        bool_array = self.df.index[
            (new_time_range[0] <= self.df[self.clean_time_col]) & (self.df[self.clean_time_col] <= new_time_range[1])]
        if len(bool_array) > 0:
            res = bool_array.values.tolist()
            res_bool = True
        else:
            res = None
            res_bool = False
        return res_bool, res

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

    def sort_and_drop_na_df(self):
        """
        Sort the dataframe and reindex it
        """
        self.df = self.df.sort_values(by=self.clean_time_col, ignore_index=True)
        self.df.drop(self.df[self.df[self.clean_time_col].isna()].index, inplace=True)
        # we'll check if it's necessary to add the img_uris to the dataframe
        if not "img_uri" in self.df:
            print("img_uri is not yet set, we'll first initialise this, hang on")
            self.set_image_uri_to_df()
        self.write_to_clean_csv("{}_clean.csv".format(os.path.splitext(self.file)[0]))

    def convert_column_first_year_via_regex(self):
        """
        convert_column_first_year_via_regex is a function that formats the "converted_creation_date" column in the pd
        dataframe to something readable
        """
        res = self.df[self.time_col].str.extract(r"([\d+]{4})").squeeze()
        self.df.insert(10, self.clean_time_col,
                       pd.to_numeric(res), True)

    def find_overlap_threaded_in_series(self, origin, indexes) -> (bool, list[dict], list[str]):
        """
        @rtype: object
        @param origin: the index in the original dataframe for which we're looking for childs in <indexes> with a textual overlap
        @param indexes: the indexes of possible children
        """

        # print("origin:")
        # print(self.df_row(origin))
        res = list()
        res_found = False

        # we'll multithread the find_overlap function to speed things up
        que = Queue()
        threads_list = list()
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
                print(Fore.GREEN + "{}".format(overlap_list) + Style.RESET_ALL)
                res.append({"index": index, "res": overlap_list, "img_uri": img_uri})
                res_found = True
            else:
                print(Fore.RED + "no textual match found" + Style.RESET_ALL)
                continue
        return res_found, res
        # todo find per column the overlaps
        # todo return: boolean 'foundsmth', which indexes with which parameters: multiple options possible!

    def find_overlap_in_series(self, origin, indexes) -> (bool, list[dict]):
        """
        @rtype: object
        @param origin:
        @param indexes:
        """

        print("origin:")
        print(self.df_row(origin))
        res = list()
        res_found = False

        for i in indexes:
            if i == origin:
                continue
            # print(self.df_row(i))
            overlap_found, overlap_list, img_uri = self.find_overlap(origin, i)
            if overlap_found:
                print(Fore.GREEN)
                print(overlap_list)
                res.append({"index": i, "res": overlap_list, "img_uri": img_uri})
                res_found = True
            else:
                # print(Fore.RED + "nothing found")
                continue
            print(Style.RESET_ALL)
        return res_found, res
        # todo find per column the overlaps
        # todo return: boolean 'foundsmth', which indexes with which parameters: multiple options possible!

    def write_to_clean_csv(self, path):
        self.df.to_csv(path)

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

    def plot_distribution(self):
        plt.figure(figsize=(20, 20))
        ax = self.df[self.clean_time_col].groupby(self.df[self.clean_time_col]).value_counts().plot(kind="bar")

        plt.title("distribution of the collection")
        plt.suptitle("Amount of pieces with a date is {}\nAmount of pieces with no date is {}".format(
            self.amount_of_valid, self.amount_of_nan))
        plt.show()

    def print_tree(self):
        print(tabulate(self.df_tree, headers='keys'))

    def get_date_from_original_df(self, idx) -> int:
        return int(self.df.iloc[idx][self.clean_time_col])

    def set_image_uri_to_df(self):
        que = Queue()
        threads_list = list()
        id_list = self.df.index.values.tolist()
        print("amount of ids to process: {}".format(len(id_list)))
        for pos, chunk in chunker(id_list, 10):
            for idx in chunk:
                t = Thread(target=lambda q, arg1, arg2: q.put(self.get_image_uri(arg1, arg2)),
                           args=(que, self.get_object_id(idx), idx))
                t.start()
                threads_list.append(t)
            for t in threads_list:
                t.join()

            while not que.empty():
                idx, img_uri = que.get()
                self.df.at[idx, "img_uri"] = img_uri
            print("{} of {} done".format(pos, len(id_list)))

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
                prev_match = i["res"]
                img_uri = i["img_uri"]
                df_temp = pd.concat([df_temp, pd.DataFrame.from_records(
                    [{"layer": self.next_layer, "df_idx": df_idx, "previous_match": prev_match, "img_uri": img_uri,
                      "parent": int(origin_idx)}])], ignore_index=True)
            return df_temp  # todo return value necessary?
        else:
            print("No matches found")
            return df_temp  # todo return value necessary?

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
                prev_match = i["res"]
                img_uri = i["img_uri"]
                self.df_tree = pd.concat([self.df_tree, pd.DataFrame.from_records(
                    [{"layer": self.next_layer, "df_idx": df_idx, "previous_match": prev_match, "img_uri": img_uri,
                      "chosen": choose_this, "has_already_been_chosen": choose_this}])],
                                         ignore_index=True)  # todo if we add the origin_idx as a column "parent" then we can calculate the entire tree structure for all possible paths, without choosing
            # print('matches had been found')
            # self.df_tree.reset_index()
            return True
            # todo perhaps we only need to set has_already_been_chosen in a backward motion
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

    def forward_build_thread(self, origin_idx):
        rows_found, row_indices = self.return_indices_in_list_range(start_idx=origin_idx,
                                                                    idx_distance=self.distance_per_step,
                                                                    idx_spread=self.spread)
        if rows_found:
            df_temp = self.forward_tree_build_no_child_chosen(row_indices=row_indices,
                                                              origin_idx=origin_idx)
            return df_temp
        else:
            return

    def build_tree_parallel(self):
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
            for pos, chunk in chunker(origin_idx_list, 10):
                thread_list_parent = list()

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

    def visualize_tree(self):
        node_list = np.array(self.steps)
        node_list[0][0] = Node(self.df_tree.loc[self.df_tree["layer"] == 0, "df_idx"])
        for layer in range(1, self.steps):
            temp_list = self.df_tree.loc[self.df_tree["layer"] == layer, "df_idx"].tolist()
            node_sub_list = list()
            for i in temp_list:
                node_sub_list.append(Node(i, parent=node_list[layer - 1][0]))
            node_list[layer] = np.array(node_sub_list)
        DotExporter(node_list[0][0]).to_picture("tree.png")

    def save_tree(self):
        self.df_tree.to_csv("{}_tree.csv".format(os.path.splitext(self.file)[0]))

    def load_tree(self):
        self.df_tree = pd.read_csv("{}_tree.csv".format(os.path.splitext(self.file)[0]))

    def get_image_uri(self, img_id, df_idx=None) -> str:
        iiif_manifest = "https://api.collectie.gent/iiif/presentation/v2/manifest/{}:{}".format(self.institute, img_id)
        try:
            req = urllib.request.Request(iiif_manifest, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req)
            # response = urlopen(iiif_manifest)
        except ValueError as e:
            print('ValueError, no image found '.format(e))
            return df_idx, None
        except HTTPError as e:
            print('HTTPError, no image found {} '.format(e))
            return df_idx, None
        else:
            data_json = json.loads(response.read())
            image_uri = data_json["sequences"][0]['canvases'][0]["images"][0]["resource"]["@id"]
            return df_idx, image_uri

    def get_object_id(self, df_tree_idx):
        # based on the index we pick the data from within our original dataframe
        res = self.df.iloc[df_tree_idx]
        # we retrieve the object number
        object_number = res["objectnumber"]
        return object_number

    def get_image_list_from_tree(self):
        # we pick the rows from our dataframe which were chose
        index_list = self.df_tree[self.df_tree["chosen"] == True].index
        # based on these indexes we pick the data from within our original dataframe
        df_list = self.df.iloc[self.df.index.isin(index_list)]
        # we make a list of the objectnumbers, as they are needed to retrieve images
        object_id_list = df_list["objectnumber"].values
        # todo improvement possible speedup if we rewrite with threads? Need to make sure order is maintained though.
        _, img_list = list(map(lambda x: self.get_image_uri(x), object_id_list))
        for i in img_list:
            print(i)
        # Using filter() method to filter None values
        filtered_img_list = list(filter(None, img_list))
        print(len(filtered_img_list))


if __name__ == '__main__':
    _file = Path(Path.cwd() / 'LDES_TO_PG' / 'data' / 'DMG.csv')
    list_cols_DMG = ['object_name', 'creator']
    stemmer_cols_DMG = ['title', 'description']
    amount_of_tissues = 100
    amount_of_imgs_to_find = math.floor(amount_of_tissues / 2)

    # 1. we make a pandas dataframe for manipulation
    fOL = FindOverlap(file=_file, institute="dmg", time_col="creation_date", list_cols=list_cols_DMG,
                      stemmer_cols=stemmer_cols_DMG,
                      steps=amount_of_imgs_to_find)
    # 2. to get some insights in the distribution of the data: enable next statement
    # fOL.plot_distribution()
    # fOL.set_image_uri_to_df()
    # 3. we search for initial objects in a time-range from the first found object
    # fOL.build_tree_parallel()
    # fOL.print_tree()
    # fOL.save_tree()
    # print("saved tree")
    # fOL.load_tree()
    # fOL.get_image_list_from_tree()

    # index_list = fOL.df_tree[fOL.df_tree["chosen"] == True].index
    # for i in index_list:
    #     print(fOL.get_image_uri(fOL.get_object_id(i)))
