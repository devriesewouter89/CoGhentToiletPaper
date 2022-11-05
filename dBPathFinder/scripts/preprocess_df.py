import argparse
import json
import math
import os
import urllib
from threading import Thread
from typing import Any, Tuple

import pandas as pd
from matplotlib import pyplot as plt
from queue import Queue
from urllib.error import HTTPError
from urllib.request import urlopen

from pathlib import Path

"""
#todo write documentation


"""


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
        """

        @param input_csv:
        @param clean_csv:
        @param institute:
        @param time_col:
        @param steps:
        """
        self.file = input_csv
        self.time_col = time_col
        self.institute = institute
        self.clean_csv = clean_csv
        self.clean_time_col = "converted_creation_date"
        self.df = pd.read_csv(input_csv, index_col=0, on_bad_lines='skip')
        self.df.drop_duplicates(inplace=True)

        self.count_err = dict()  # {"403": 0, "404": 0, "500": 0, "502": 0}
        # 1. the dates are not easily human-readable, let's convert them
        if not self.clean_time_col in self.df:
            self.convert_column_first_year_via_regex()
        self.amount_of_entries = 0
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
        if 'timestamp' in self.df:
            self.df.drop(columns="timestamp", inplace=True)
        self.df.drop_duplicates(subset="image", inplace=True)
        # we'll check if it's necessary to add the img_uris to the dataframe
        if "img_uri" not in self.df:
            print("img_uri is not yet set, we'll first initialise this, hang on")
            self.set_image_uri_to_df()
        self.amount_of_entries = len(self.df)
        print("Before image filtering, {} entries".format(self.amount_of_entries))
        if '0' in self.df:
            self.df.drop(columns='0', inplace=True)
        self.df.drop(self.df[self.df["img_uri"].isna()].index, inplace=True)
        self.df.reset_index(drop=True, inplace=True)
        print("after filtering, {} entries left".format(len(self.df)))
        self.write_to_clean_csv(self.clean_csv)

    def get_iiif_manifest(self, df_tree_idx):
        """based on the index we pick the data from within our original dataframe
        attention, we use .loc, not .iloc as our index is not one continuous integer array!
        """
        res = self.df.loc[df_tree_idx]
        # we retrieve the object number
        iiif_manifest = res["image"]
        return iiif_manifest

    def convert_column_first_year_via_regex(self):
        """
        convert_column_first_year_via_regex is a function that formats the "converted_creation_date" column in the pd
        dataframe to something readable
        """
        # extract the date from the time_col
        res = self.df[self.time_col].str.extract(r"([\d+]{4})").squeeze()
        # in the provenance_date col, sometimes we get nan's, we replace these with empty strings
        if "provenance_date" in self.df:
            self.df["provenance_date"] = self.df["provenance_date"].fillna("")
            # we then also extract a possible date of the provenance_date col
            res2 = self.df["provenance_date"].str.extract(r"([\d+]{4})").squeeze()
            # from the provenance date, we remove values below 1000
            res2.where(res2.astype('Int64') > 1000, inplace=True)
            # we give priority to the time_col, yet use the provenance_date as a backup date
            res_combined = res.where(res.notnull(), res2)
        else:
            res_combined = res
        # sometimes in the title there's also date information
        res3 = self.df["description"].str.extract(r"([\d+]{4})").squeeze()
        res_combined = res_combined.where(res_combined.notnull(), res3)
        self.df.insert(self.df.shape[1], self.clean_time_col,
                       pd.to_numeric(res_combined), True)

    def plot_distribution(self):
        plt.figure(figsize=(20, 20))
        try:
            ax = self.df[self.clean_time_col] \
                .groupby(self.df[self.clean_time_col]) \
                .value_counts() \
                .plot(kind="bar")
        except:
            print("not enough values?")
        plt.title("distribution of the collection")
        plt.suptitle(
            "StartAmount: {}\nAmount of pieces with a date is {}\n"
            "Amount of pieces with no date is {} \n errors: {}".format(
                self.amount_of_entries, self.amount_of_valid,
                self.amount_of_nan, self.count_err))
        # plt.show()
        plt.savefig("{}.jpg".format(os.path.splitext(self.clean_csv)[0]))

    def write_to_clean_csv(self, path):
        self.df.to_csv(path)

    def set_image_uri_to_df(self):
        que = Queue()
        threads_list = []  # list()
        id_list = self.df.index.values.tolist()
        print("amount of ids to process: {}".format(len(id_list)))

        for pos, chunk in chunker(id_list, 100):
            for idx in chunk:
                t = Thread(target=lambda q, arg1, arg2, arg3: q.put(self.get_image_uri(arg1, arg2, arg3)),
                           args=(que, self.get_iiif_manifest(idx), idx, self.count_err,))
                t.start()
                threads_list.append(t)
            for t in threads_list:
                t.join()
            count_error_temp = {"403": 0, "404": 0, "502": 0}
            while not que.empty():
                idx, img_uri, count_error_temp = que.get()
                self.df.at[idx, "img_uri"] = img_uri
            # count_err = dict(map(lambda x, y: (x[0], x[1]+y[1]), count_err.items(), count_error_temp.items()))
            count_err = count_error_temp
            print("{} of {} done".format(pos, len(id_list)))
        print("of {} ids, we got next HTTP errors: {}".format(
            len(id_list), self.count_err))

    def get_image_uri(self, iiif_manifest, df_idx=None, count_err=None) -> tuple[Any, None, dict] | \
                                                                           tuple[Any, Any, dict]:
        # iiif_manifest = "https://api.collectie.gent/iiif/presentation/v2/manifest/{}:{}".format(
        #     self.institute.lower(), img_id).replace(" ", "%20") # todo is de replace nodig of is er een fout in de brondata?

        try:
            req = urllib.request.Request(iiif_manifest, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=10)
            print("got response from {}".format(iiif_manifest))

            # response = urlopen(iiif_manifest)
        except ValueError as e:
            # print('ValueError, no image found {}: {}'.format(e, iiif_manifest))
            return df_idx, None, count_err
        except HTTPError as e:
            print('HTTPError, no image found {} for {}'.format(e, iiif_manifest))
            if str(e.code) not in count_err:
                new_error_code = {str(e.code): 1}
                count_err.update(new_error_code)
            else:
                count_err[str(e.code)] += 1
            return df_idx, None, count_err
        else:
            data_json = json.loads(response.read())
            image_uri = data_json["sequences"][0]['canvases'][0]["images"][0]["resource"]["@id"]
            # adapt image_uri for specific resolution
            # iiif_manifest = iiif_manifest.replace("full/full/0/default.jpg", "full/1000,/0/default.jpg")
            return df_idx, image_uri, count_err


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', '-dp', default=Path(Path.cwd().parent / 'data'))
    parser.add_argument("--dataset", '-ds', help="choose collections to preprocess",
                        choices=["dmg", "im", "stam", "hva",
                                 "archiefgent", "thesaurus", "AGENT"], default=["industriemuseum"])
    args = parser.parse_args()

    data_path = Path(args.data_path)
    datasets = args.dataset
    for dataset in datasets:
        input_file = Path(data_path / '{}.csv'.format(dataset))
        clean_data_path = Path(data_path / "clean_data")
        clean_data_path.mkdir(parents=True, exist_ok=True)
        clean_file = Path(clean_data_path / '{}.csv'.format(dataset))

        list_cols = ['object_name']#  'creator']
        stemmer_cols = ['title', 'description']
        amount_of_tissues = 100
        amount_of_imgs_to_find = math.floor(amount_of_tissues / 2)
        # 1. we make a pandas dataframe for manipulation
        clean_df = PrepDf(input_csv=input_file, clean_csv=clean_file, institute=dataset, time_col="creation_date",
                          steps=amount_of_imgs_to_find)

        # 2. to get some insights in the distribution of the data: enable next statement
        clean_df.plot_distribution()

