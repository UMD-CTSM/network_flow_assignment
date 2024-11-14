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
class GeoDataNetwork:
  nodeDf : gpd.GeoDataFrame
  edgeDf : gpd.GeoDataFrame
  LABEL : str
  # The weight column to use
  network_weight_fn : Callable[ [pd.DataFrame], pd.Series ]

  # First column: from, second column: to
  network_link_fn : Callable[ [pd.DataFrame], pd.DataFrame ]

  network_node_fn : Callable[
    [tuple[Hashable, pd.Series], pd.DataFrame], tuple[Hashable, dict]
  ] = lambda rrow, LABEL, df :  (
    int(rrow[0]),
    {'id': int(rrow[0]), 'label': rrow[1][LABEL], 'y': rrow[1].geometry.y, 'x': rrow[1].geometry.x}
  )


  def createNetwork(self, write_to=None, skip=[20, 159], NAME=None):
    network = nx.Graph(name=NAME)
    network.add_nodes_from(self.createNodeList(skip))
    network.add_weighted_edges_from(self.createLinkList())
    if write_to is not None:
      nx.write_gml(network, write_to)
    return network
  
  def createNodeList(self, skip) -> list:
    node_list = []
    for rrow in self.nodeDf.iterrows():
      if int(rrow[0]) in skip: continue
      node_list.append(self.network_node_fn(rrow, self.LABEL, self.nodeDf))
    return node_list

  def createLinkList(self) -> List[tuple[Hashable, dict, Number]]:
    linksDf = self.network_link_fn(self.edgeDf)
    linksDf['weight'] = self.network_weight_fn(self.edgeDf)
    return linksDf.values.tolist()
