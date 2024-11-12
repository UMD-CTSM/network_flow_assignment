import networkx as nx
from dataclasses import dataclass
import geopandas as gpd
import pandas as pd
from pandas import Series
from pathlib import Path
from shapely import LineString
import numpy as np
import math

from typing import Callable, Hashable, Dict, List
from numbers import Number

from IPython.display import display

@dataclass
class FafZoneNetwork:
  naRailNodesDf : gpd.GeoDataFrame
  naRailLinesDf : gpd.GeoDataFrame
  fafZonesDf : gpd.GeoDataFrame

  # FAF_ZONE_COLNAME : str = 'FAF_Zone'
  FRA_NODE_ID_COLNAME : str = 'FRANODEID'
  FRFRANODE_COLNAME : str = 'FRFRANODE'
  TOFRANODE_COLNAME : str = 'TOFRANODE'

  def setInputDfColType(self):
    self.fafZonesDf = self.fafZonesDf.astype({'FAF_Zone': int})
    return self

  _naRailNodesWithFafZonesDf : gpd.GeoDataFrame = None
  @property
  def naRailNodesWithFafZonesDf(self) -> gpd.GeoDataFrame:
    if self._naRailNodesWithFafZonesDf is None:
      self._naRailNodesWithFafZonesDf = self.naRailNodesDf.sjoin(
        self.fafZonesDf,
        how='left',
        predicate="within"
      ).set_index(self.FRA_NODE_ID_COLNAME)
    return self._naRailNodesWithFafZonesDf
  
  _fafZoneNodesDf : gpd.GeoDataFrame = None
  @property
  def fafZoneNodesDf(self) -> gpd.GeoDataFrame:
    if self._fafZoneNodesDf is None:
      fafZoneNodesDf = self.naRailNodesWithFafZonesDf.dropna(subset=['FAF_Zone']).dissolve(['FAF_Zone'])
      fafZoneNodesDf.geometry = fafZoneNodesDf.to_crs(epsg=3857).centroid.to_crs(4326)
      self._fafZoneNodesDf = fafZoneNodesDf
    return self._fafZoneNodesDf

  FR : str = '_fr'
  TO : str = '_to'

  _naRailLinesWithFafZonesDf : gpd.GeoDataFrame = None
  @property
  def naRailLinesWithFafZonesDf(self) -> gpd.GeoDataFrame:
    if self._naRailLinesWithFafZonesDf is None:
      nodeIdIndexFZDf = self.naRailNodesWithFafZonesDf

      naRailLinesWithFafZonesDf = self.naRailLinesDf.join(
        nodeIdIndexFZDf.add_suffix(self.FR), on=self.FRFRANODE_COLNAME
      ).join(
        nodeIdIndexFZDf.add_suffix(self.TO), on=self.TOFRANODE_COLNAME
      )

      naRailLinesWithFafZonesDf = naRailLinesWithFafZonesDf[naRailLinesWithFafZonesDf.columns[
        ~(
          naRailLinesWithFafZonesDf.columns.str.endswith(self.FR)
          | naRailLinesWithFafZonesDf.columns.str.endswith(self.TO)
        )
      ].union(['FAF_Zone_fr', 'FAF_Zone_to'])]
      self._naRailLinesWithFafZonesDf = naRailLinesWithFafZonesDf
    return self._naRailLinesWithFafZonesDf

  link_aggregation_fn = 'count'

  _fafZoneLinksDf : gpd.GeoDataFrame = None
  @property
  def fafZoneLinksDf(self) -> gpd.GeoDataFrame:
    if self._fafZoneLinksDf is None:
      fafZoneLinksDf = self.naRailLinesWithFafZonesDf[
        self.naRailLinesWithFafZonesDf.FAF_Zone_fr != self.naRailLinesWithFafZonesDf.FAF_Zone_to
      ]
      flippedLinks = fafZoneLinksDf.FAF_Zone_fr > fafZoneLinksDf.FAF_Zone_to
      fafZoneLinksDf.loc[
        flippedLinks, ['FAF_Zone_fr', 'FAF_Zone_to']
      ] = fafZoneLinksDf.loc[flippedLinks, ['FAF_Zone_to', 'FAF_Zone_fr']].values
      fafZoneLinksDf = fafZoneLinksDf.dissolve(
        by=['FAF_Zone_fr', 'FAF_Zone_to'],
        aggfunc=self.link_aggregation_fn
      )
      fafZoneLinksDf.index = fafZoneLinksDf.index.set_levels([l.astype(int) for l in fafZoneLinksDf.index.levels])
      fafZoneLinksDf = fafZoneLinksDf.join(self.fafZoneNodesDf.add_suffix('_fr'), on='FAF_Zone_fr')
      fafZoneLinksDf = fafZoneLinksDf.join(self.fafZoneNodesDf.add_suffix('_to'), on='FAF_Zone_to')
      fafZoneLinksDf.geometry = fafZoneLinksDf.apply(lambda r:  LineString([
          [r.geometry_fr.x, r.geometry_fr.y],
          [r.geometry_to.x, r.geometry_to.y]
      ]), axis=1)
      self._fafZoneLinksDf = fafZoneLinksDf
    return self._fafZoneLinksDf

  def createNetwork(self, write_to=None, skip=[20, 159]):
    railnet = nx.Graph()
    railnet.add_nodes_from(self.createNodeList(skip))
    railnet.add_weighted_edges_from(self.createLinkList())
    if write_to is not None:
      nx.write_gml(railnet, write_to)
    return railnet


  network_node_fn : Callable[
    [tuple[Hashable, pd.Series], pd.DataFrame], tuple[Hashable, dict]
  ] = lambda rrow, df : (
    int(rrow[0]),
    {'faf_id': int(rrow[0]), 'label': rrow[1].FAF_Zone_1, 'y': rrow[1].geometry.y, 'x': rrow[1].geometry.x}
  )
  def createNodeList(self, skip) -> list:
    node_list = []
    for rrow in self.fafZoneNodesDf.iterrows():
      if int(rrow[0]) in skip: continue
      node_list.append(self.network_node_fn(rrow, self.fafZoneNodesDf))
    return node_list
  
  network_weight_fn : Callable[ [pd.DataFrame], pd.Series ] = lambda df : df['FRAARCID']

  network_link_fn : Callable[ [pd.DataFrame], pd.DataFrame
  ] = lambda df : df.reset_index()[['FAF_Zone_fr','FAF_Zone_to']]

  def createLinkList(self) -> List[tuple[Hashable, dict, Number]]:
    linksDf = self.network_link_fn(self.fafZoneLinksDf)
    self.fafZoneLinksDf['weight'] = self.network_weight_fn(self.fafZoneLinksDf)
    linksDf['weight'] = self.fafZoneLinksDf['weight'].values
    
    return linksDf.values.tolist()
  
  def apply_flows(self, flow_dict):
    self.fafZoneLinksDf['flows'] = [flow_dict[x] for x in self.fafZoneLinksDf.index]
    return self.fafZoneLinksDf
  
  def apply_flows_from_network(self, railnet_flows : nx.Graph):
    return self.apply_flows({e : railnet_flows.edges[e]['weight'] for e in railnet_flows.edges})
    
def normalize( df : pd.Series):
  return (df - df.min() ) / (df.max() - df.min())
def normalize_reverse( df : pd.Series):
  return (df.max() - df ) / (df.max() - df.min())

def link_weights(df : gpd.GeoDataFrame):
  df['distance'] = df['geometry_fr'].to_crs(3857).distance(df['geometry_to'].to_crs(3857))
  df['distance_norm'] = normalize_reverse(df['distance'])
  df['n_tracks_norm'] = normalize_reverse(df['FRAARCID'])
  return df[['n_tracks_norm', 'distance_norm']].sum(axis=1)

if __name__ == "__main__":
  import argparse
  
  parser = argparse.ArgumentParser()
  
  parser.add_argument("rail_network_lines", help = "Input rail network lines shapefile")
  parser.add_argument("rail_network_nodes", help = "Input rail network nodes shapefile")
  parser.add_argument("faf_zones", help = "Input FAF zones shapefile")
  # Read arguments from command line
  args = parser.parse_args()

  print("Reading")

  CreateFafZoneNetwork(
    naRailLinesDf = gpd.read_file( Path.cwd() / args.rail_network_lines ),
    naRailNodesDf = gpd.read_file( Path.cwd() / args.rail_network_nodes ),
    fafZonesDf = gpd.read_file( Path.cwd() / args.faf_zones ).to_crs(3857)
  ).createNetwork()
