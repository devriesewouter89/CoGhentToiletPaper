import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas
import pandas as pd
from supabase_py import client
from dotenv import load_dotenv
import os
from os.path import join, dirname
import csv


def upload_data(csv_path: Path, sb: client, location: str):
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


def get_sb_data(sb: client, location: str) -> pandas.DataFrame:
    # todo only get 1000 results at once, implement jump with offset
    query = sb.table(location).select("*")
    data2 = query.execute()
    data1 = json.dumps(data2.get("data"), indent=2)
    data = pd.read_json(data1, typ="frame")
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', '-dp', default=Path(Path.cwd().parent / 'data'))
    parser.add_argument("--dataset", '-ds',
                        help="choose collections to preprocess",
                        choices=["dmg", "industriemuseum", "stam", "hva",
                                 "archiefgent", "thesaurus", "AGENT"],
                        default=["industriemuseum", "hva", "archiefgent"])
    args = parser.parse_args()

    data_path = Path(args.data_path)

    dotenv_path = join(dirname(__file__), '../.env')
    load_dotenv(dotenv_path)

    # warning, make sure your key is the secret key, not anon key if row level policy is enabled.
    URL = os.environ.get("URL")
    KEY = os.environ.get("KEY")
    sb = client.create_client(supabase_url=URL, supabase_key=KEY)

    datasets = args.dataset
    print("start supa injection at {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    for dataset in datasets:
        # upload_data(Path(Path.cwd().parent / 'data' / 'clean_data'), sb, dataset)
        df = get_sb_data(sb, dataset)
        print(df.head())
