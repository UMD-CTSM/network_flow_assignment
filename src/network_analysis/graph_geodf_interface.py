import networkx as nx
import geopandas as gpd
import shapely
from pathlib import Path

# railnet = nx.read_gml('../../resources/networks/faf_railnet_withtraffic.gml')
# faf_network_nodes_shapefile_name = f'../../resources/shapefiles/faf_network_nodes.shp'
# faf_network_edges_shapefile_name = f'../../resources/shapefiles/faf_network_edges.shp'

  # faf_network_edges_gdf.to_file(faf_network_edges_shapefile_name, )
class GraphGeopd:
  def __init__(self, railnet : nx.Graph):
    self.railnet = railnet
    self.nodes = self.create_node_geodf()
    self.edges = self.create_edge_geodf(self.nodes)

  def create_node_geodf(self) -> gpd.GeoDataFrame:
    faf_network_nodes_gdf = gpd.GeoDataFrame.from_records([self.railnet.nodes[i] for i in self.railnet.nodes])
    faf_network_nodes_gdf = faf_network_nodes_gdf.set_geometry(gpd.points_from_xy(faf_network_nodes_gdf.lon, faf_network_nodes_gdf.lat))
    faf_network_nodes_gdf = faf_network_nodes_gdf.set_index('faf_id')
    faf_network_nodes_gdf = faf_network_nodes_gdf.drop(columns=['lon', 'lat'], axis=1)
    faf_network_nodes_gdf = faf_network_nodes_gdf.set_crs(epsg=4269)
    return faf_network_nodes_gdf

  def create_edge_geodf(self, faf_network_nodes_gdf : gpd.GeoDataFrame ):
    edge_list = []
    for fro, to in self.railnet.edges:
      fro_node = faf_network_nodes_gdf.loc[int(fro)]
      to_node = faf_network_nodes_gdf.loc[int(to)]
      
      edge_list.append({
        'to': to,
        'fro': fro,
        'weight': self.railnet.edges[(fro,to)]['weight'],
        'geometry': shapely.LineString((
          (fro_node.geometry.x,fro_node.geometry.y),
          (to_node.geometry.x,to_node.geometry.y)
        ))
      })

    faf_network_edges_gdf = gpd.GeoDataFrame(edge_list)
    faf_network_edges_gdf = faf_network_edges_gdf.set_crs(epsg=4269)
    return faf_network_edges_gdf

  def graph_to_shapefile(self, railnet: nx.Graph):
    self.graph_to_geodf(railnet)


# if __name__ == "__main__":
#   import argparse
  
#   parser = argparse.ArgumentParser()
#   file_dir = Path(__file__).resolve().parent

#   parser.add_argument("input_graph", help = "Input network as a .gml file")
#   GraphGeopd()