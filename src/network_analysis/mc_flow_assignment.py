import pandas as pd
import scipy
import numpy as np


rng = np.random.default_rng()
def sample_flows( flowDf : pd.DataFrame, BASE_COLUMN : str, distribution = 'triangular'):
  HIGH_COLUMN = BASE_COLUMN + '_high'
  LOW_COLUMN = BASE_COLUMN + '_low'

  from IPython.display import display

  randomNeededIndex = flowDf[LOW_COLUMN] != flowDf[HIGH_COLUMN]
  flowSeries = flowDf[BASE_COLUMN].copy()
  randomNeededDf = flowDf[randomNeededIndex][[HIGH_COLUMN, LOW_COLUMN, BASE_COLUMN]]
  if distribution == 'triangular':
    flowSeries[randomNeededIndex] = rng.triangular(
      left=randomNeededDf[LOW_COLUMN].to_list(),
      mode=randomNeededDf[BASE_COLUMN].to_list(),
      right=randomNeededDf[HIGH_COLUMN].to_list()
    )
  elif distribution == 'normal':
    right_point96 = (randomNeededDf[LOW_COLUMN] + (randomNeededDf[BASE_COLUMN] - randomNeededDf[LOW_COLUMN]) * 2 + randomNeededDf[HIGH_COLUMN]) / 2
    std_dev = (right_point96 - randomNeededDf[BASE_COLUMN]) / 3
    flowSeries[randomNeededIndex] = rng.normal(
      loc=randomNeededDf[BASE_COLUMN].to_list(),
      scale=std_dev.to_list()
    )
  else:
    raise Exception("Distribution unsupported: " + distribution)
  
  return flowSeries 

