# Other Scripts

This folder contains helper scripts and references for Assignment 3.

## OpenSearch

The `opensearch/` folder contains:

- `sample_mapping.json` — mapping used for the `photos` index
- `query_examples.json` — query examples for independent label, custom label, and group label search
- `search_query_builder.py` — Python helper draft for LF2 search query construction

## Search behavior supported by OpenSearch index

The `photos` index supports:

1. Independent label search  
   Example: `dog`

2. Custom label search  
   Example: `testlabel`

3. Group label search  
   Example: `dog and park`

LF1 normalizes labels before indexing by lowercasing, trimming, deduplicating, and adding simple singular versions where useful.