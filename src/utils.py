import pandas as pd
def fr(s : str, suffix = '_fr'):
  return s + suffix

def to(s : str, suffix = '_to'):
  return s + suffix

    
def normalize( df : pd.Series):
  return (df - df.min() ) / (df.max() - df.min())
def normalize_reverse( df : pd.Series):
  return (df.max() - df ) / (df.max() - df.min())