from lodstorage.sparql import SPARQL
from lodstorage.csv import CSV
import pandas as pd
from pathlib import Path

"""
to build the query: 
1. go to an object of the collection: eg https://data.collectie.gent/entity/stam:S.1158 
2. Click on "Meer info over dit werk" 
3. Click on the link at the bottom 
    This shows the different CIDOC properties that one can request to browse through the data collection. 
    This way, you can also link queries to get to deeper layers of the 
object (e.g. https://coghent.github.io/basicqueries.html#union getting to ?maker 
"""


def launch_query(location: str, csv_output: Path, df_return: bool = False):
    sparql_query = (
            """
    PREFIX cidoc:<http://www.cidoc-crm.org/cidoc-crm/>
    PREFIX adms:<http://www.w3.org/ns/adms#>
    PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
    SELECT DISTINCT ?title ?description ?image ?object_name ?creation_date ?location ?maker
    
    FROM <http://stad.gent/ldes/%s>
    WHERE {
        ?object cidoc:P102_has_title ?title.
        ?object cidoc:P3_has_note ?description.
        ?object cidoc:P129i_is_subject_of ?image.
        ?object cidoc:P41i_was_classified_by ?classified.
        ?classified cidoc:P42_assigned ?assigned.
        ?assigned skos:prefLabel ?object_name.
        ?object adms:identifier ?identifier.
        ?object cidoc:P108i_was_produced_by ?production .
        ?production cidoc:P14_carried_out_by ?maker .
        ?production cidoc:P4_has_time-span ?creation_date.
        ?production cidoc:P7_took_place_at ?location.
        ?identifier skos:notation ?objectnumber.
    } 
    LIMIT 100000
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
    location = "industriemuseum"
    csv_location = Path(Path.cwd().parent / "data")
    csv_location.mkdir(parents=True, exist_ok=True)
    df = launch_query(location, csv_output=Path(csv_location / "{}.csv".format(location)), df_return=True)
    pd.set_option('display.max_columns', None)
    print(df.head(5))
