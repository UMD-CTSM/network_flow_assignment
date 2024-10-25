# network_flow_assignment

## Setup
1. [Install miniconda](https://docs.anaconda.com/miniconda/miniconda-install/)
2. Create environment `conda env create -f environment.yml`
3. Activate the environment `conda activate network_flow_assignment`
4. (If using `geoprocessing`) Set the `ARCGIS_PROJECT` env variable `export ARCGIS_PROJECT=<PROJECT LOCATION>`
5. Populate the `inputs` directory with necessary files (Directory structure below)

## Inputs directory structure


## Default run commands
python src/flow_assignment/flow_assignment.py resources/networks/faf_railnet.gml inputs/faf_freight_flow.csv