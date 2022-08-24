'''
python file to check two or more lines from a csv file

'''
import pandas as pd
from stemmer import sentence_to_stems
from pathlib import Path
import ast
import numpy as np
from datetime import date
import re

class FindOverlap:
    def __init__(self, file, time_col: str, list_cols: [str], stemmer_cols: [str]):
        """

        @type stemmer_cols: array of strings
        @type list_cols: array of strings
        """
        self.file = file
        self.time_col = time_col
        self.list_cols = list_cols
        self.stemmer_cols = stemmer_cols
        self.df = pd.read_csv(file)

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
        new_time_range = [date(new_origin - time_spread, 1, 1), date(new_origin + time_spread, 1, 1)]
        print(new_time_range)
        # for i in range(1, 20):
        #     print("index {}".format(i))
        #     cell = self.df[self.time_col].iloc[i]
        #     # print(cell, type(cell))
        #     year_cell = self.extract_first_year_via_regex(cell)
        #     print("year_cell = {}".format(year_cell))
        #     year_cell_date = date(year_cell, 1, 1)
        #     print(new_time_range[0] < year_cell_date < new_time_range[1])
        #     print()
        bool_array = self.df.loc[(new_time_range[0] <= date(self.extract_first_year_via_regex(self.df[self.time_col]), 1, 1))]
        print(bool_array)
        # res = self.df.loc[] # < new_time_range[1]]
        # return res

    def convert_column_first_year_via_regex(self):
        # try:
        ser = self.df[self.time_col]
        # print(ser.str.extract(r'([\d+]{4})'))
        self.df['converted_creation_date']= self.df[self.time_col].str.extract(r"([\d+]{4})")
        #     date_find = re.findall(r"[\d+]{4}", text)
        #     print(date_find, text)
        #     if date_find:
        #         return int(date_find[0])
        #     else:
        #         return 1
        # except:
        #     return 1
        print(self.df['converted_creation_date'].head())

# def find_overlappers(file, origin, indexes) -> list():
#     """
#     TODO not satisfied with this, not functionally written!
#     @param file:
#     @param origin:
#     @param indexes:
#     """
#     df = pd.read_csv(file)
#     # print("origin:")
#     print(df.iloc[origin, :])
#     for i in indexes:
#         # print(df.iloc[i, :])
#         overlap_found, overlap_list = find_overlap(df.iloc[origin, :], df.iloc[i, :])
#         if overlap_found:
#             print(overlap_list)
#         else:
#             print("nothing found")
#     # todo find per column the overlaps
#     # todo return: boolean 'foundsmth', which indexes with which parameters: multiple options possible!


if __name__ == '__main__':
    _file = Path(Path.cwd() / 'LDES_TO_PG' / 'data' / 'DMG.csv')
    print(_file)
    list_cols_DMG = ['object_name', 'creator']
    stemmer_cols_DMG = ['title', 'description']
    fOL = FindOverlap(file=_file, time_col="creation_date", list_cols=list_cols_DMG, stemmer_cols=stemmer_cols_DMG)
    # print(fOL.find_overlap(28, 29))
    # row_indices = fOL.find_indices_in_time_range(1870, 14, 15)
    # print(row_indices.head())
    fOL.convert_column_first_year_via_regex()