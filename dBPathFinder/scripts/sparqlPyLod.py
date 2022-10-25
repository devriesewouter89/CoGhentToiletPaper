from lodstorage.sparql import SPARQL
from lodstorage.csv import CSV
import pandas as pd
from pathlib import Path


def launch_query(location: str, csv_output: Path, df_return: bool = False):
    sparql_query = ("""
    PREFIX cidoc:<http://www.cidoc-crm.org/cidoc-crm/>
    PREFIX adms:<http://www.w3.org/ns/adms#>
    PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
    SELECT DISTINCT *
    #?title ?note ?image ?objectname ?objectnumber ?creation_date
    
    FROM <http://stad.gent/ldes/%s>
    WHERE {
        # ?o cidoc:P102_has_title ?title.
        # ?o cidoc:P3_has_note ?note.
        # ?o cidoc:P129i_is_subject_of ?image.
        # ?o cidoc:P14_carried_out_by ?actor.
        # ?o cidoc:P41i_was_classified_by ?classified.
        # ?classified cidoc:P42_assigned ?assigned.
        # ?assigned skos:prefLabel ?objectname.
        # ?o adms:identifier ?identifier.
        # ?identifier skos:notation ?objectnumber.
    } 
        """ % location)

    sparql = SPARQL("https://stad.gent/sparql")
    qlod = sparql.queryAsListOfDicts(sparql_query)
    csv = CSV.toCSV(qlod)
    with open(csv_output, 'w') as out:
        out.write(csv)
    if df_return:
        # csv = [x.split('","') for x in csv.split('"\r\n')]
        df_result = pd.DataFrame([x.split('","') for x in csv.split('"\r\n')])
        # remove " in first column
        df_result.iloc[:, 0] = df_result.iloc[:, 0].str.replace('"', '')
        # set headers back
        df_result.rename(columns=df_result.iloc[0, :], inplace=True)
        df_result.drop(df_result.index[0], inplace=True)

        # remove duplicates
        df_result.drop_duplicates(inplace=True)
        print(df_result.shape)
        return df_result


if __name__ == '__main__':
    location = "dmg"
    csv_location = Path(Path.cwd().parent / "data")
    csv_location.mkdir(parents=True, exist_ok=True)
    df = launch_query(location, csv_output=Path(csv_location / "{}.csv".format(location)), df_return=True)
    pd.set_option('display.max_columns', None)
    print(df.head(5))
