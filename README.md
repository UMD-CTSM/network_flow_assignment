# network_flow_assignment

## Setup
1. [Install miniconda](https://docs.anaconda.com/miniconda/miniconda-install/)
2. Create environment `conda env create -f environment.yml`
3. Activate the environment `conda activate network_flow_assignment`
4. (If using `geoprocessing`) Set the `ARCGIS_PROJECT` env variable `export ARCGIS_PROJECT=<PROJECT LOCATION>`
5. Populate the `inputs` directory with necessary files (Directory structure below)

## Inputs directory structure
```
- 2017_CFS_Metro_Areas_with_FAF: FAF Zone geodata from https://faf.ornl.gov/faf5/data/2017_CFS_Metro_Areas_with_FAF.zip
- NTAD_North_American_Rail_Network_Lines: Rail Network geodata from https://geodata.bts.gov/datasets/usdot::north-american-rail-network-lines/about
- NTAD_North_American_Rail_Network_Nodes: Rail Network geodata from https://geodata.bts.gov/datasets/usdot::north-american-rail-network-nodes/about
- faf_freight_flow.csv: Tons from https://faf.ornl.gov/faf5/dtt_total.aspx from/to all origins
```

## Default run commands
python src/flow_assignment/flow_assignment.py resources/networks/faf_railnet.gml inputs/faf_freight_flow.csv