import os
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
from pathlib import Path


def launch_query(location: str, csv_output: Path):
    def return_query(location, offset):
        sparql_query = (
                """
        PREFIX cidoc:<http://www.cidoc-crm.org/cidoc-crm/>
        PREFIX adms:<http://www.w3.org/ns/adms#>
        PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
        SELECT DISTINCT ?title ?manifest ?description ?creation_date ?object_name 

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
        return sparql_query

    sparql = SPARQLWrapper("https://stad.gent/sparql")

    sparql.setReturnFormat(JSON)
    df = pd.DataFrame(columns=['title', 'image', 'descr', 'creation_date'])
    for i in range(1000):
        query = return_query(location=location, offset=i)
        try:
            print(i)
            sparql.setQuery(query)
            ret = sparql.queryAndConvert()
            for r in ret["results"]["bindings"]:
                # print(r)
                title = r.get('title').get('value')
                manifest = r.get('manifest').get('value')
                descr = r.get('description').get('value')
                creation_date = r.get('creation_date').get('value')
                df = pd.concat([df, pd.DataFrame.from_records(
                    [{'title': title, 'manifest': manifest, 'description': descr, 'creation_date': creation_date}])])
        except Exception as e:
            print(e)
    df.to_csv(csv_output)

if __name__ == '__main__':
    location = "stam"
    csv_location = Path(Path.cwd().parent / "data")
    csv_location.mkdir(parents=True, exist_ok=True)
    csv_output_file = Path(csv_location / "{}_sparql.csv".format(location))
    if csv_output_file.exists():
        os.remove(csv_output_file)
    launch_query(location, csv_output=csv_output_file)
