from dBPathFinder.findOverlap import FindOverlap
from pathlib import Path
import pandas as pd


def test_find_overlap():
    _file = Path(Path.cwd() / 'LDES_TO_PG' / 'data' / 'DMG.csv')
    print(_file)
    assert _file
    df = pd.read_csv(_file)
    index_origin = 28
    index_to_find = 29
    list_cols = ['object_name', 'creator']
    stemmer_cols = ['title', 'description']
    fOL = FindOverlap(file=_file, time_col="", list_cols=list_cols, stemmer_cols=stemmer_cols)
    assert fOL
    res_found, res_list = fOL.find_overlap(index_origin, index_to_find)
    assert res_found
    assert res_list[0]['column'] == 'object_name'
    assert res_list[0]['overlap'] == ['studie']
    index_to_find = 8
    res_found, res_list = fOL.find_overlap(index_origin, index_to_find)
    assert not res_found
    assert not res_list

