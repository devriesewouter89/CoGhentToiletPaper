'''
python file to check two or more lines from a csv file

'''
import pandas as pd
from stemmer import sentence_to_stems
from pathlib import Path
import ast
import numpy as np


def find_overlappers(file, origin, indexes) -> list():
    df = pd.read_csv(file)
    # print("origin:")
    print(df.iloc[origin, :])
    for i in indexes:
        # print(df.iloc[i, :])
        overlap_found, overlap_list = find_overlap(df.iloc[origin, :], df.iloc[i, :])
        if overlap_found:
            print(overlap_list)
        else:
            print("nothing found")
    # todo find per column the overlaps
    # todo return: boolean 'foundsmth', which indexes with which parameters: multiple options possible!


def find_overlap(origin, target) -> (bool, list[str]):
    # todo replace list[str] with a list of dicts? this way we capture the column name as well
    overlap_found = False
    overlap_list = list[str]()
    list_cols = ['object_name', 'creator']
    stemmer_cols = ['title', 'description']
    for col in list_cols:
        # we need to unpack the strings to list via ast.literal_eval as otherwise we're evaluating character-based.
        # we use the try except statement as not always there are valid entries
        try:
            origin_entries = ast.literal_eval(origin[col])
            target_entries = ast.literal_eval(target[col])
            res = list(set(origin_entries).intersection(target_entries))
            if res:
                overlap_found = True
                overlap_list.append(res)
        except Exception as e:
            # print(e)
            pass
    for col in stemmer_cols:
        try:
            df1_res = sentence_to_stems(origin[col])
            df2_res = sentence_to_stems(target[col])
            res = list(set(df1_res).intersection(df2_res))
            if res:
                overlap_found = True
                overlap_list.append(res)
        except Exception as e:
            print(e)
            pass
    return overlap_found, overlap_list


if __name__ == '__main__':
    _file = Path(Path.cwd() / 'LDES_TO_PG' / 'data' / 'DMG.csv')
    print(_file)
    find_overlappers(_file, 28, [29, 30])
