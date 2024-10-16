from dataclasses import dataclass

import networkx as nx
import pandas as pd
from pathlib import Path

@dataclass
class FlowAssignment:
  SUM_COLUMN : str
  def assign_segments(self, railnet : nx.Graph) -> pd.DataFrame:
    shortest_paths = nx.all_pairs_shortest_path(railnet)
    path_segment_list = []
    for origin, paths in shortest_paths:
      for dest in paths:
        if dest == origin: continue
        path = paths[dest]
        for segment_i in range(len(path) - 1):
          path_segment_list.append({
            'dms_orig': origin,
            'dms_dest': dest,
            'seg_start': path[segment_i],
            'seg_end': path[segment_i + 1]
          })

    path_segments = pd.DataFrame(path_segment_list)
    path_segments = path_segments.astype(int)
    path_segments = path_segments.set_index(['dms_orig', 'dms_dest'])
    return path_segments

  def faf_flows_to_df(self, faf_flows : pd.DataFrame) -> pd.DataFrame:
    faf_flows = faf_flows.astype(int)
    faf_flows_by_pair = faf_flows.groupby(['dms_orig', 'dms_dest']).agg({self.SUM_COLUMN: ['sum']})
    faf_flows_by_pair.columns = faf_flows_by_pair.columns.map('_'.join)
    return faf_flows_by_pair

  def merge_segments_flows(self, path_segments : pd.DataFrame, faf_flows_by_pair : pd.DataFrame) -> pd.DataFrame:
    path_segments_w_traffic = path_segments.copy()
    path_segments_w_traffic = path_segments.join(faf_flows_by_pair)
    segment_traffic = path_segments_w_traffic.groupby(['seg_start', 'seg_end']).agg({self.SUM_COLUMN + '_sum':['sum']})
    return segment_traffic

  def apply_flows(self, railnet : nx.Graph, segment_traffic : pd.DataFrame) -> nx.Graph:
    for (start, end), traffic in segment_traffic.iterrows():
      railnet.edges[(start, end)]['weight'] = float(traffic[self.SUM_COLUMN + '_sum']['sum'])
    return railnet

  def run(self, railnet, input_flows : pd.DataFrame):
    path_segments = self.assign_segments(railnet)
    faf_flows_by_pair = self.faf_flows_to_df(input_flows)
    segment_traffic = self.merge_segments_flows(path_segments, faf_flows_by_pair)

    railnet = self.apply_flows(railnet, segment_traffic)
    return railnet

if __name__ == "__main__":
  import argparse
  
  parser = argparse.ArgumentParser()
  
  parser.add_argument("input_graph", help = "Input network as a .gml file")
  parser.add_argument("input_flows", help = "Input flows as a csv")
  parser.add_argument("-c", "--sum_column", help = "Column to use as flow", default='thousand tons in 2050')
  parser.add_argument("-o", "--output_graph", help = "Where to put the output graph", default="./output.gml")

  # Read arguments from command line
  args = parser.parse_args()

  fa = FlowAssignment(SUM_COLUMN=args.sum_column)
  nx.write_gml(fa.run(
    nx.read_gml(Path.cwd() / args.input_graph),
    pd.read_csv(Path.cwd() / args.input_flows)
  ), args.output_graph)
  

