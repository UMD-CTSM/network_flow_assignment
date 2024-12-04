from dataclasses import dataclass
from typing import Any

import networkx as nx
import pandas as pd
from pathlib import Path

class FlowAssignment:
  def __init__(self, railnet : nx.Graph) -> None:
    self.path_segments = self.assign_segments(railnet)

  def assign_segments(self, railnet : nx.Graph) -> pd.DataFrame:
    shortest_paths = nx.all_pairs_shortest_path(railnet)
    path_segment_list = []
    for origin, paths in shortest_paths:
      for dest in paths:
        if dest == origin: continue
        path = paths[dest]
        for segment_i in range(len(path) - 1):
          path_segment_list.append({
            'dms_orig': origin if origin < dest else dest,
            'dms_dest': dest if origin < dest else origin,
            'seg_start': path[segment_i],
            'seg_end': path[segment_i + 1],
            'seg_start_degree': railnet.degree[path[segment_i]],
            'seg_end_degree': railnet.degree[path[segment_i + 1]]
          })

    path_segments = pd.DataFrame(path_segment_list)
    path_segments = path_segments.astype(int)
    path_segments = path_segments.set_index(['dms_orig', 'dms_dest', 'seg_start', 'seg_end'])
    return path_segments

  def faf_flows_to_df(self, faf_flows : pd.DataFrame, SUM_COLUMN) -> pd.DataFrame:
    faf_flows = faf_flows.astype(int)
    
    # Flip flows
    larger_first_flows = faf_flows.dms_orig > faf_flows.dms_dest
    faf_flows.loc[larger_first_flows, ['dms_orig', 'dms_dest']] = faf_flows.loc[larger_first_flows, ['dms_dest', 'dms_orig']].values
    faf_flows_by_pair = faf_flows.groupby(['dms_orig', 'dms_dest']).agg({SUM_COLUMN: ['sum']})
    faf_flows_by_pair.columns = faf_flows_by_pair.columns.map('_'.join)
    
    # Filter out flows with no value
    faf_flows_by_pair = faf_flows_by_pair.loc[faf_flows_by_pair[SUM_COLUMN + '_sum'] > 0]
    return faf_flows_by_pair
  
  def add_inter_zone_flows(self, path_segments : pd.DataFrame, faf_flows_by_pair : pd.DataFrame, SUM_COLUMN) -> pd.DataFrame:

    # Flip segments
    reversed_segs = path_segments.seg_start > path_segments.seg_end
    path_segments.loc[reversed_segs, ['seg_start', 'seg_end']] = path_segments.loc[reversed_segs, ['seg_end', 'seg_start']]
    
    path_segments_w_traffic = path_segments.join(faf_flows_by_pair)
    return self.merge_flows(path_segments_w_traffic, SUM_COLUMN)
  
  def merge_flows(self, path_segments_w_traffic : pd.DataFrame, SUM_COLUMN) -> pd.DataFrame:
    segment_traffic = path_segments_w_traffic.groupby(['seg_start', 'seg_end']).agg({SUM_COLUMN + '_sum':['sum']})
    return segment_traffic[SUM_COLUMN + '_sum']['sum']

  def add_intra_zone_flows(self, segment_traffic : pd.DataFrame, faf_flows_by_pair : pd.DataFrame, SUM_COLUMN) -> pd.DataFrame:
    intra_zone_flows = faf_flows_by_pair.loc[faf_flows_by_pair.index.get_level_values('dms_orig') == faf_flows_by_pair.index.get_level_values('dms_dest')]
    intra_zone_flows = intra_zone_flows.reset_index(1, drop=True)[SUM_COLUMN + '_sum']
    segment_traffic = segment_traffic.reset_index()
    segment_traffic = segment_traffic.join(intra_zone_flows, on='seg_start').rename(columns={SUM_COLUMN + '_sum': SUM_COLUMN + '_sum_start'})
    segment_traffic = segment_traffic.join(intra_zone_flows, on='seg_end').rename(columns={SUM_COLUMN + '_sum': SUM_COLUMN + '_sum_end'})
    
    segment_traffic = segment_traffic.fillna(0)
    segment_traffic['new_sum'] = (
      segment_traffic[SUM_COLUMN + '_sum_start'] / segment_traffic['seg_start_degree']  +
      segment_traffic[SUM_COLUMN + '_sum_end'] / segment_traffic['seg_end_degree']
    )
    return self.merge_flows(segment_traffic, 'new')

  def __call__(self, *args: Any, **kwds: Any) -> Any:
    return self.run(*args, **kwds)

  def run(self, input_flows : pd.DataFrame = None, SUM_COLUMN = '', faf_flows_by_pair=None):
    if faf_flows_by_pair is None:
      faf_flows_by_pair = self.faf_flows_to_df(input_flows, SUM_COLUMN)
    return (
      # self.merge_segments_flows(self.path_segments, faf_flows_by_pair, SUM_COLUMN)
      self.add_intra_zone_flows(self.path_segments, faf_flows_by_pair, SUM_COLUMN)
    )
  
if __name__ == "__main__":
  import argparse
  
  parser = argparse.ArgumentParser()
  
  parser.add_argument("input_graph", help = "Input network as a .gml file")
  parser.add_argument("input_flows", help = "Input flows as a csv")
  parser.add_argument("-c", "--sum_column", help = "Column to use as flow", default='thousand tons in 2050')
  parser.add_argument("-o", "--output_graph", help = "Where to put the output graph", default="./output.gml")

  # Read arguments from command line
  args = parser.parse_args()

  fa = FlowAssignment(nx.read_gml(Path.cwd() / args.input_graph))
  nx.write_gml(fa.run(
    pd.read_csv(Path.cwd() / args.input_flows),
    SUM_COLUMN=args.sum_column
  ), args.output_graph)
  

