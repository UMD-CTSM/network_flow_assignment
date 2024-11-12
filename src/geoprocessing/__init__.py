
import pandas as pd
def order_link_nodes(linkDf : pd.DataFrame, START_COL : str, END_COL : str):
  reversed_segs = linkDf[START_COL] > linkDf[END_COL]
  reversed_seg_ends = linkDf.loc[reversed_segs, END_COL]
  reversed_seg_starts = linkDf.loc[reversed_segs, START_COL]

  linkDf.loc[reversed_segs, START_COL] = reversed_seg_ends
  linkDf.loc[reversed_segs, END_COL] = reversed_seg_starts
  return linkDf
  

# def create_network(nodeDf : pd.DataFrame, linkDf : pd.DataFrame):
