'''
python file to check two or more lines from a csv file

'''
import math
import random

import pandas as pd
from matplotlib import pyplot as plt

from stemmer import sentence_to_stems
from pathlib import Path
import ast
from datetime import date
from colorama import Fore, Style
from tabulate import tabulate


class FindOverlap:
    def __init__(self, file, time_col: str, list_cols: list[str], stemmer_cols: list[str], steps: int):
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
        print("Initial reading of the data: {}".format(self.df.describe))
        self.end_date: int = date.today().year
        self.steps = steps
        self.object_tree = list()
        self.df_tree = pd.DataFrame(columns=["layer", "df_idx", "previous_match", "chosen", "has_already_been_chosen"])
        self.start_date: int = 0  # start_date we want to retrieve from the clean_time_col
        self.start_object = None
        self.start_idx: int = 0
        self.next_date = 0
        self.next_layer = 0
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
                res.append({"index": i, "res": overlap_list})
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
        # print(self.df[self.clean_time_col].dropna().min())
        idx = self.df[self.clean_time_col].idxmin(skipna=True)
        self.start_idx = idx
        self.start_object = self.df.iloc[idx]
        self.start_date = self.df.iloc[idx][self.clean_time_col]
        self.df_tree = pd.concat([self.df_tree, pd.DataFrame.from_records(
            [{"layer": 0, "df_idx": self.start_idx, "previous_match": "", "chosen": True,
              "has_already_been_chosen": True}])])

    def plot_distribution(self):
        plt.figure(figsize=(20, 20))
        ax = self.df[self.clean_time_col].groupby(self.df[self.clean_time_col]).value_counts().plot(kind="bar")
        amount_of_valid = self.df[self.clean_time_col].count()
        amount_of_nan = self.df[self.clean_time_col].isna().sum()
        plt.title("distribution of the collection")
        plt.suptitle("Amount of pieces with a date is {}\nAmount of pieces with no date is {}".format(amount_of_valid,
                                                                                                      amount_of_nan))
        plt.show()

    def print_tree(self):
        for layer, res in self.object_tree[0].items():
            print(layer)
            for object in res:
                for index, match in object.items():
                    print("---> index: {}, date is: {}".format(index, int(self.df.iloc[index][self.clean_time_col])))
                    for overlap in match:
                        print("---------> {}".format(overlap))

    def get_date_from_original_df(self, idx) -> int:
        return int(self.df.iloc[idx][self.clean_time_col])

    def build_tree(self):
        print(tabulate(self.df_tree, headers='keys'))
        # todo: split this in a forward motion and backward motion when no options can be found in next layer
        for layer in range(1, self.steps):
            chosen_in_previous_layer = self.df_tree[
                (self.df_tree["layer"] == layer - 1) & (self.df_tree['chosen'])]
            origin_idx = chosen_in_previous_layer["df_idx"].values[0]
            origin_year = self.get_date_from_original_df(origin_idx)
            rows_found, row_indices = self.find_indices_in_time_range(origin_year=origin_year, time_distance=50,
                                                                      time_spread=49) #todo lets make time_distance be decided by the spread of the data
            if rows_found:
                print("{} indices found".format(len(row_indices)))
                # 4. we remove the start index if present and check if we find semantic matches
                # FORWARD MOTION todo: add BACKWARDS motion
                if origin_idx in row_indices:
                    print('found original object, removing it')
                    row_indices.remove(origin_idx)
                if len(row_indices) < 1:
                    print("no results")
                matches_found, matches = self.find_overlap_in_series(origin_idx, row_indices)
                if matches_found:
                    print("{} matches found for layer {}".format(len(matches), layer))
                    # we choose a random start option
                    choose_idx = random.randint(0, len(matches) - 1)
                    for idx, i in enumerate(matches):
                        if idx == choose_idx:
                            choose_this = True
                        else:
                            choose_this = False
                        df_idx = i["index"]
                        prev_match = i["res"]
                        self.df_tree = pd.concat([self.df_tree, pd.DataFrame.from_records(
                            [{"layer": layer, "df_idx": df_idx, "previous_match": prev_match, "chosen": choose_this,
                              "has_already_been_chosen": choose_this}])])  # todo perhaps we only need to set has_already_been_chosen in a backward motion
                else:
                    print("we came at a dead-end by no matches found, return a layer and try another index")
                    print(tabulate(self.df_tree, headers='keys'))
            else:
                print("we came at a dead end, there were no indices found in the timezone")
                print("end result:")
                print(tabulate(self.df_tree, headers='keys'))
                print('last date found: {}'.format(self.get_date_from_original_df(self.df_tree[self.df_tree["layer"] == layer - 1]["df_idx"])))
        print(tabulate(self.df_tree, headers='keys'))


if __name__ == '__main__':
    _file = Path(Path.cwd() / 'LDES_TO_PG' / 'data' / 'STAM.csv')
    list_cols_DMG = ['object_name', 'creator']
    stemmer_cols_DMG = ['title', 'description']
    amount_of_tissues = 100
    amount_of_imgs_to_find = math.floor(amount_of_tissues / 2)

    # 1. we make a pandas dataframe for manipulation
    fOL = FindOverlap(file=_file, time_col="creation_date", list_cols=list_cols_DMG, stemmer_cols=stemmer_cols_DMG,
                      steps=amount_of_imgs_to_find)
    # 2. to get some insights in the distribution of the data: enable next statement
    fOL.plot_distribution()
    # 3. we search for initial objects in a time-range from the first found object
    fOL.build_tree()
    # fOL.print_tree()

    # clean_csv_path = Path(Path.cwd() / 'LDES_TO_PG' / 'data' / 'DMG_clean.csv')
    # fOL.write_to_clean_csv(clean_csv_path)
