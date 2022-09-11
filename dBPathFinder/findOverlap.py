'''
python file to check two or more lines from a csv file

'''
import math

import pandas as pd
from matplotlib import pyplot as plt

from stemmer import sentence_to_stems
from pathlib import Path
import ast
import numpy as np
from datetime import date
import re
from colorama import Fore, Style
import pprint


class FindOverlap:
    def __init__(self, file, time_col: str, list_cols: list[str], stemmer_cols: list[str]):
        """

        @type stemmer_cols: array of strings
        @type list_cols: array of strings
        """
        self.file = file
        self.time_col = time_col
        self.clean_time_col = "converted_creation_date"
        self.list_cols = list_cols
        self.stemmer_cols = stemmer_cols
        self.df = pd.read_csv(file).drop_duplicates()
        self.end_date: int = date.today().year
        self.start_date: int = None  # start_date we want to retrieve from the clean_time_col
        self.start_object = None
        self.start_idx: int = None
        # 1. the dates are not easily human readable, let's convert them
        self.convert_column_first_year_via_regex()
        # 2. let's set the starting point of our path
        self.find_first_entry()

    def find_overlap(self, origin_idx, target_idx) -> (bool, list[dict]):
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
        return overlap_found, overlap_list

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
        # print(new_time_range)
        bool_array = self.df.index[
            (new_time_range[0] <= self.df[self.clean_time_col]) & (self.df[self.clean_time_col] <= new_time_range[1])]
        if len(bool_array) > 0:
            res = bool_array.values.tolist()
            res_bool = True
        else:
            res = None
            res_bool = False
        # print(bool_array)
        return res_bool, res

    def convert_column_first_year_via_regex(self):
        """
        convert_column_first_year_via_regex is a function that formats the "converted_creation_date" column in the pd dataframe to something readable
        """
        res = self.df[self.time_col].str.extract(r"([\d+]{4})").squeeze()
        self.df.insert(10, self.clean_time_col,
                       pd.to_numeric(res), True)
        # print(self.df[self.clean_time_col].head())

    def find_overlap_in_series(self, origin, indexes) -> (bool, list[dict]):
        """
        TODO not satisfied with this, not functionally written!
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
            overlap_found, overlap_list = self.find_overlap(origin, i)
            if overlap_found:
                print(Fore.GREEN)
                print(overlap_list)
                res.append({i: overlap_list})
                res_found = True
            else:
                print(Fore.RED + "nothing found")
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
        print(self.df[self.clean_time_col].dropna().min())
        idx = self.df[self.clean_time_col].idxmin(skipna=True)
        self.start_idx = idx
        self.start_object = self.df.iloc[idx]
        self.start_date = self.df.iloc[idx][self.clean_time_col]

    def plot_distribution(self):
        plt.figure(figsize=(20, 20))
        ax = self.df[self.clean_time_col].groupby(self.df[self.clean_time_col]).value_counts().plot(kind="bar")
        amount_of_valids = self.df[self.clean_time_col].count()
        amount_of_nan = self.df[self.clean_time_col].isna().sum()
        plt.title("distribution of the collection")
        plt.suptitle("Amount of pieces with a date is {}\nAmount of pieces with no date is {}".format(amount_of_valids,
                                                                                                      amount_of_nan))
        plt.show()


def print_tree(tree):
    for layer, res in tree[0].items():
        print(layer)
        for object in res:
            for index, match in object.items():
                print("---> index: {}".format(index))
                for overlap in match:
                    print("---------> {}".format(overlap))


if __name__ == '__main__':
    _file = Path(Path.cwd() / 'LDES_TO_PG' / 'data' / 'DMG.csv')
    list_cols_DMG = ['object_name', 'creator']
    stemmer_cols_DMG = ['title', 'description']
    amount_of_tissues = 100
    amount_of_imgs_to_find = math.floor(amount_of_tissues / 2)

    # 1. we make a pandas dataframe for manipulation
    fOL = FindOverlap(file=_file, time_col="creation_date", list_cols=list_cols_DMG, stemmer_cols=stemmer_cols_DMG)
    # 2. to get some insights in the distribution of the data: enable next statement
    # fOL.plot_distribution()
    # 3. we search for initial objects in a time-range from the first found object
    layer = 0
    object_tree = list()
    res_found, row_indices = fOL.find_indices_in_time_range(fOL.start_date, time_distance=50, time_spread=50)
    # 4. we remove the start index if present and check if
    if fOL.start_idx in row_indices:
        print('found original object, removing it')
        row_indices.remove(fOL.start_idx)
    if len(row_indices) < 1:
        print("no results")
    res_found, res = fOL.find_overlap_in_series(fOL.start_idx, row_indices)
    if (res_found):
        object_tree.append({layer: res})
        # now we have to choose an option and continue
    else:
        print("we came at a dead-end, return a layer and try another index")
    print_tree(object_tree)
    # 4. Next we want to continue searching to get our path
    # clean_csv_path = Path(Path.cwd() / 'LDES_TO_PG' / 'data' / 'DMG_clean.csv')
    # fOL.write_to_clean_csv(clean_csv_path)
