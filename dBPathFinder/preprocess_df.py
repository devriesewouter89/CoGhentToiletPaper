import json
import os
import urllib
from threading import Thread
from typing import Any

import pandas as pd
from matplotlib import pyplot as plt
from queue import Queue
from urllib.error import HTTPError
from urllib.request import urlopen


def chunker(seq, size):
    """
    function to iterate over lists in chunks, useful for massive threadlists
    @param seq:
    @param size:
    @return:
    """
    return ((pos, seq[pos:pos + size]) for pos in range(0, len(seq), size))


class PrepDf:
    def __init__(self, input_csv, clean_csv, institute: str, time_col: str, steps: int):
        self.file = input_csv
        self.time_col = time_col
        self.institute = institute
        self.clean_csv = clean_csv
        self.clean_time_col = "converted_creation_date"
        self.df = pd.read_csv(input_csv, index_col=0).drop_duplicates()

        # 1. the dates are not easily human-readable, let's convert them
        if not self.clean_time_col in self.df:
            self.convert_column_first_year_via_regex()

        self.set_dtypes()
        # 2. sort the dataframe and drop the elements which have no clear date
        self.sort_and_drop_na_df()

        self.amount_of_valid = self.df[self.clean_time_col].count()
        self.amount_of_nan = self.df[self.clean_time_col].isna().sum()

    def set_dtypes(self):
        self.df[self.clean_time_col] = pd.to_numeric(self.df[self.clean_time_col], downcast='integer')

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
        # self.write_to_clean_csv("{}_clean.csv".format(os.path.splitext(self.file)[0]))
        print("Before image filtering, {} entries".format(len(self.df)))
        self.df.drop(columns='0', inplace=True)
        self.df.drop(self.df[self.df["img_uri"].isna()].index, inplace=True)
        self.df.reset_index(drop=True, inplace=True)
        print("after filtering, {} entries left".format(len(self.df)))
        self.write_to_clean_csv(self.clean_csv)

    def get_object_id(self, df_tree_idx):
        # based on the index we pick the data from within our original dataframe
        res = self.df.iloc[df_tree_idx]
        # we retrieve the object number
        object_number = res["objectnumber"]
        return object_number

    def convert_column_first_year_via_regex(self):
        """
        convert_column_first_year_via_regex is a function that formats the "converted_creation_date" column in the pd
        dataframe to something readable
        """
        res = self.df[self.time_col].str.extract(r"([\d+]{4})").squeeze()
        res2 = self.df["provenance_date"].str.extract(r"([\d+]{4})").squeeze()
        res2.where(res2.astype('Int64') > 1000, inplace=True)
        res_combined = res.where(res.notnull(), res2)
        self.df.insert(10, self.clean_time_col,
                       pd.to_numeric(res_combined), True)

    def plot_distribution(self):
        plt.figure(figsize=(20, 20))
        try:
            ax = self.df[self.clean_time_col].groupby(self.df[self.clean_time_col]).value_counts().plot(kind="bar")
        except:
            print("not enough values?")
        plt.title("distribution of the collection")
        plt.suptitle("Amount of pieces with a date is {}\nAmount of pieces with no date is {}".format(
            self.amount_of_valid, self.amount_of_nan))
        plt.show()

    def write_to_clean_csv(self, path):
        self.df.to_csv(path)

    def set_image_uri_to_df(self):
        que = Queue()
        threads_list = []  # list()
        id_list = self.df.index.values.tolist()
        print("amount of ids to process: {}".format(len(id_list)))
        for pos, chunk in chunker(id_list, 100):
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

    def get_image_uri(self, img_id, df_idx=None) -> tuple[Any, None] | tuple[Any, Any]:
        iiif_manifest = "https://api.collectie.gent/iiif/presentation/v2/manifest/{}:{}".format(self.institute.lower(),
                                                                                                img_id)
        print(iiif_manifest)
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
