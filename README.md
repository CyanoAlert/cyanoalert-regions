# cyanoalert-regions

CyanoAlert region data and scripts.

Requirements

- python 3.6+
- fiona
- shapely

Install env:

    $ conda create -n cyanoalert python=3.6 fiona shapely

Run scripts:

    $ source activate cyanoalert
    $ python scripts/write-geojson.py
    $ python scripts/read-geojson.py


