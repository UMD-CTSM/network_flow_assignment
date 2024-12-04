import networkx as nx
from dataclasses import dataclass
import geopandas as gpd
import pandas as pd
from .utils import fr, to
from scipy import stats

import folium
import branca.colormap as cm

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

  VALUE : str = 'flows'

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
  
  def calculate_centrality(self, network=None, weighted=True):
    if network is None:
      network = self.createNetwork()
    self.apply_link_property('centrality', dict(nx.edge_betweenness_centrality(network, weight='weight' if weighted else None)))
    self.apply_node_property('centrality', dict(nx.betweenness_centrality(network, weight='weight' if weighted else None)))
  
  def createNodeList(self, skip=[]) -> list:
    node_list = []
    for rrow in self.nodeDf.iterrows():
      if int(rrow[0]) in skip: continue
      node_list.append(self.network_node_fn(rrow, self.LABEL, self.nodeDf))
    return node_list

  def createLinkList(self) -> List[tuple[Hashable, dict, Number]]:
    linksDf = self.network_link_fn(self.edgeDf)
    linksDf['weight'] = self.network_weight_fn(self.edgeDf)
    return linksDf.values.tolist()

  
  def apply_link_property(self, value_name, value_dict, apply_to_node = True):
    self.edgeDf[value_name] = [value_dict.get(x, None) for x in self.edgeDf.index]
    if apply_to_node:
      link_flows = self.edgeDf.groupby('FAF_Zone_fr').agg({value_name: 'sum'}).add_suffix('_fr').join(
        self.edgeDf.groupby('FAF_Zone_to').agg({value_name: 'sum'}).add_suffix('_to'),
        how='outer'
      ).fillna(0)
      self.nodeDf[value_name] = (link_flows[value_name + '_fr'] + link_flows[value_name + '_to']) / 2
      self.nodeDf[value_name] = self.nodeDf[value_name].fillna(0)
    return self
  
  def apply_node_property(self, value_name, value_dict):
    self.nodeDf[value_name] = [value_dict.get(x, None) for x in self.nodeDf.index]
    return self

  def remove_na(self):
    self.nodeDf = self.nodeDf.dropna(axis='index', subset=self.VALUE)
    self.edgeDf = self.edgeDf.dropna(axis='index', subset=[
      self.VALUE
    ] if self.VALUE in self.edgeDf.columns else [fr(self.VALUE), to(self.VALUE)])

  link_normalizer = None
  node_normalizer = None
  def create_normalizers(self, link_distrib=stats.uniform, node_distrib=stats.uniform, default_zero=False):
    self.remove_na()
    if self.link_normalizer is None:
      link_flows = self.edgeDf[self.VALUE]
      self.link_normalizer = Normalizer(link_flows, link_distrib, default_zero=default_zero)
    if self.node_normalizer is None:
      node_flows = self.nodeDf[self.VALUE]
      self.node_normalizer = Normalizer(node_flows, node_distrib, default_zero=default_zero)


  def show_map(self, zone_df=False, color_nodes=False):
    
    self.create_normalizers()

    min_lat=24.7433195
    max_lat=49.3457868
    min_lon=-124.7844079
    max_lon=-66.9513812


    m = folium.Map(
      max_bounds=True,
      location=[42, -95],
      zoom_start=4,
      min_zoom=4,
      tiles='OpenStreetMap',
      # max_lat=max_lat,
      # min_lon=min_lon,
      # max_lon=max_lon,
      # min_lat=min_lat
    )


    # flows.apply(distrib.cdf).plot(kind='hist', bins=50)

    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    lineWeightMax = 5
    lineWeightMin = 0.5

    if zone_df:
      zone_df.geometry = zone_df.geometry.simplify(.15)
      zone_df[[self.LABEL, 'geometry']].explore(
        m=m,
        column=self.LABEL,
        cmap='Greens',
        legend=False,
        style_kwds={'opacity':.1}
      )

    if False: 
      from folium import DivIcon
      for i, r in fzn.edgeDf.iterrows():
        center = r.geometry.centroid
        folium.map.Marker(
          [center.y, center.x],
          icon=DivIcon(
              icon_size=(20,150),
              icon_anchor=(0,0),
              html='<div style="font-size: 12px">%s</div>' % round(r.flows,4),
            )
        ).add_to(m)


      for i, r in fzn.nodeDf.iterrows():
        center = r.geometry.centroid
        folium.map.Marker(
          [center.y, center.x],
          icon=DivIcon(
              icon_size=(20,150),
              icon_anchor=(0,0),
              html='<div style="font-size: 16px; font-weight: bold">%s</div>' % int(i),
            )
        ).add_to(m)

    get_flow = lambda feature : feature['properties'][self.VALUE]
    self.edgeDf[[self.LABEL + '_fr', self.LABEL + '_to', self.VALUE, 'geometry']].explore(
      m=m,
      column=self.VALUE,
      style_kwds={
        'style_function': lambda feature: {
          'color': cm.linear.plasma(self.link_normalizer(get_flow(feature))),
          'weight': self.link_normalizer(get_flow(feature)) * (lineWeightMax - lineWeightMin) + lineWeightMin
        }
      },
      legend=True,
      legend_kwds={
        'legend_name': 'Tons of Freight Transported',
      }
    )


    self.nodeDf[[self.LABEL, self.VALUE, 'geometry']].explore(
      m=m,
      color='black',
      style_kwds={
        'style_function': lambda feature: {
          'color': cm.linear.plasma(self.node_normalizer(get_flow(feature))) if color_nodes else 'black',
          'weight': self.node_normalizer(get_flow(feature)) * (lineWeightMax - lineWeightMin) + lineWeightMin
        }
      }
    )

    return m

  def show_values(self):
    display(self.nodeDf[[self.LABEL, self.VALUE]].sort_values(self.VALUE, ascending=False).head(10))
    display(self.edgeDf[[self.LABEL + '_fr', self.LABEL + '_to', self.VALUE]].sort_values(self.VALUE, ascending=False).head(10))

class Normalizer:
  def __init__(self, data : pd.Series, distrib_obj=stats.genexpon, default_zero = False):
    distrib_params = distrib_obj.fit(data)
    self.distrib = distrib_obj(*distrib_params)
    self.default_zero = default_zero
  def __call__(self, x):
    if self.default_zero and x <= 0:
      return 0
    return self.distrib.cdf(x)
