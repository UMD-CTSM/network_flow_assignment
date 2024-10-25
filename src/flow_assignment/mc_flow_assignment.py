import pandas as pd
import scipy
import numpy as np


rng = np.random.default_rng()
def sample_flows( flowDf : pd.DataFrame, BASE_COLUMN : str):
  HIGH_COLUMN = BASE_COLUMN + '_high'
  LOW_COLUMN = BASE_COLUMN + '_low'

  from IPython.display import display

  randomNeededIndex = flowDf[LOW_COLUMN] != flowDf[HIGH_COLUMN]
  flowSeries = flowDf[BASE_COLUMN].copy()
  randomNeededDf = flowDf[randomNeededIndex][[HIGH_COLUMN, LOW_COLUMN, BASE_COLUMN]]
  flowSeries[randomNeededIndex] = rng.triangular(
    left=randomNeededDf[LOW_COLUMN].to_list(),
    mode=randomNeededDf[BASE_COLUMN].to_list(),
    right=randomNeededDf[HIGH_COLUMN].to_list()
  )
  
  return flowSeries 

