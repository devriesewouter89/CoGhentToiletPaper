import os
from datetime import datetime
from itertools import zip_longest

import SPARQLWrapper.SPARQLExceptions
from lodstorage.sparql import SPARQL
from lodstorage.csv import CSV
import pandas as pd
from pathlib import Path

from src.config_toilet import Config

"""
to build the query: 
1. go to an object of the collection: eg https://data.collectie.gent/entity/stam:S.1158 
2. Click on "Meer info over dit werk" 
3. Click on the link at the bottom 
    This shows the different CIDOC properties that one can request to browse through the data collection. 
    This way, you can also link queries to get to deeper layers of the 
object (e.g. https://coghent.github.io/basicqueries.html#union getting to ?maker 
"""


# https://api.collectie.gent/iiif/image/iiif/2/1f28135dd9a495db544d9f702729afac-transcode-V04548-014.jpg/full/full/0/default.jpg

def launch_query(location: str, csv_output: Path, df_return: bool = False):
    def return_query(location, offset):
        sparql_query = (
                """
        PREFIX cidoc:<http://www.cidoc-crm.org/cidoc-crm/>
        PREFIX adms:<http://www.w3.org/ns/adms#>
        PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
        SELECT DISTINCT ?object ?title ?manifest ?description ?creation_date ?object_name 
        
        FROM <http://stad.gent/ldes/%s>
        WHERE {
            ?object cidoc:P102_has_title ?title.
            ?object cidoc:P129i_is_subject_of ?manifest.
            ?object cidoc:P3_has_note ?description.
            ?object cidoc:P108i_was_produced_by ?production.       
            ?production cidoc:P4_has_time-span ?creation_date. 
            # OPTIONAL {
            # ?object cidoc:P41i_was_classified_by ?classified.
            # ?classified cidoc:P42_assigned ?assigned.
            # ?assigned skos:prefLabel ?object_name.       
            # }
            
        } 
        LIMIT 1000
        OFFSET %s
        """ % (location, str(offset * 1000)))

        sparql_query2 = (
                """
        PREFIX cidoc:<http://www.cidoc-crm.org/cidoc-crm/>
        PREFIX adms:<http://www.w3.org/ns/adms#>
        PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
        SELECT DISTINCT ?object ?object_name 

        FROM <http://stad.gent/ldes/%s>
        WHERE {         
            ?object cidoc:P41i_was_classified_by ?classified.
            ?classified cidoc:P42_assigned ?assigned.
            ?assigned skos:prefLabel ?object_name.       
        } 
        LIMIT 1000
        OFFSET %s
        """ % (location, str(offset * 1000)))

        return sparql_query, sparql_query2

    print('launching query for {}'.format(location))
    sparql = SPARQL("https://stad.gent/sparql")
    df = pd.DataFrame()
    for i in range(1000):
        # we have multiple queries, as one big query is too slow for the back-end
        query, query2 = return_query(location=location, offset=i)
        try:
            qlod = sparql.queryAsListOfDicts(query)
            qlod2 = sparql.queryAsListOfDicts(query2)
            # we'll combine the two qlods to stitch the results
            qlod3 = [{**u, **v} for u, v in zip_longest(qlod, qlod2, fillvalue={})]
            csv = CSV.toCSV(qlod3)
            print("{}: got results in csv, writing them now".format(i))
            with open(csv_output, 'a+') as out:
                out.write(csv)
            if df_return:
                # csv = [x.split('","') for x in csv.split('"\r\n')]
                df_result = pd.DataFrame([x.split('","') for x in csv.split('"\r\n')])
                # remove " in first column
                df_result.iloc[:, 0] = df_result.iloc[:, 0].str.replace('"', '')
                # set headers back
                df_result.rename(columns=df_result.iloc[0, :], inplace=True)
                df_result.drop(df_result.index[0], inplace=True)
                df = pd.concat([df, df_result])
        except IndexError as e:
            print(e)
            break
        except SPARQLWrapper.SPARQLExceptions.SPARQLWrapperException as e:
            print(e)
            continue
    # remove duplicates
    df.drop_duplicates(inplace=True)
    print(df.shape)
    return df


if __name__ == '__main__':
    config = Config()
    print("start fetching data at {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    config.location_files.mkdir(parents=True, exist_ok=True)
    csv_output_file = config.raw_data_path
    if csv_output_file.exists():
        os.remove(csv_output_file)
    df = launch_query(config.location, csv_output=csv_output_file, df_return=True)
    pd.set_option('display.max_columns', None)
    print(df.head(5))
