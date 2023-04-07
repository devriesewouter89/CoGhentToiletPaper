# database path finder

Finding a path in linked data is not trivial. There is no straightforward way as far as I know.
My first approach would be to try to summarize the database metrics and rank the different metrics.
This way, finding a path by prioritizing entries of metrics could have more chance of being a path that can actually found.


## link to the differing databases

Olivier already did write a script to fetch the LDES stream and place it into a tabular dataframe (postgresQL, csv, excel):
[https://github.com/oliviervd/LDES_TO_PG](https://github.com/oliviervd/LDES_TO_PG)

## scripts

1. make sure the data is in supabase:
   1. [sparqlPyLod.py](./scripts/sparqlPyLod.py): get data from coghent database
   2. [preprocess_df.py](./scripts/preprocess_df.py): fetch image URIs and append 
   3. [supabase_link.py](./scripts/supabase_link.py): inject it into a supabase (stability issues with coghent database)
2. fetch the preprocessed dataframe from supabase:
   1. [supabase_link.py](./scripts/supabase_link.py)
3. find a path in the dataframe:
   4. [findoverlap.py](findOverlap.py)

# supabase

