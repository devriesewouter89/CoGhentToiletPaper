import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv
import os
from os.path import join, dirname
import csv
from config_toilet import Config


def upload_data(csv_path: Path, sb: Client, location: str):
    with open(Path(csv_path / "{}.csv".format(location))) as f:
        csv_data = list(csv.DictReader(f, delimiter=','))

    data_to_db = []
    for row in csv_data:
        data_to_db.append(
            {'id': int(row[""]),
             'title': row["title"],
             'manifest': row["manifest"],
             'description': row["description"],
             'creation_date': int(float(row["converted_creation_date"])),
             'object_name': row["object_name"],
             'img_uri': row["img_uri"]
             }
        )
    # generate query towards
    query = sb.table(location).insert(data_to_db)
    response = query.execute()
    print(response)


def get_sb_data(sb: Client, location: str) -> pandas.DataFrame:
    # todo only get 1000 results at once, implement jump with offset
    offset = 0
    df = pd.DataFrame()
    while True:
        print('from', offset)
        query = sb.table(location).select("*").gt('id', str(offset))
        data2 = query.execute()
        # Assert we pulled real data.

        if len(data2.data) > 1:
            offset += 1000
            data1 = json.dumps(data2.data, indent=2)
            data = pd.read_json(data1, typ="frame")
            print(data.head)
            df = pd.concat([df, data])
        else:
            print("went up to {}".format(offset))
            break
    return df

def link_supabase(config) -> Client:

    sb = create_client(supabase_url=config.URL, supabase_key=config.KEY)
    return sb

if __name__ == '__main__':
    config = Config()
    sb = link_supabase(config)

    # print("start supa injection at {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    # upload_data(config.clean_data_path, sb, config.location)

    print("start supa extraction at {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    df = get_sb_data(sb, config.location)
    print(df.head())
    print(df.info)
