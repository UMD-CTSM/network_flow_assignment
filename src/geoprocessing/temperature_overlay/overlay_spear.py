from pathlib import Path
import geopandas as gpd
import netCDF4
import xarray as xr
from shapely import ops

basePath = Path.cwd().parent / 'inputs'
diffNcPath = basePath / 'spear_tas_diff.nc'


def load_tas_diff(path = diffNcPath):
  tasDiffdf = xr.open_dataset(path).to_dataframe()
  # tasDiffdf.index.names =['geo_center_x_zone', 'geo_center_y_zone']
  tasDiffdf = tasDiffdf.reset_index()
  tasDiffdf.loc[tasDiffdf.lon > 180, 'lon'] = tasDiffdf.lon -360
  tasDiffdf = gpd.GeoDataFrame(
    tasDiffdf, geometry=gpd.points_from_xy(tasDiffdf.lon, tasDiffdf.lat), crs="epsg:4326"
  )

  return tasDiffdf

def join_tas_diff(featureDf : gpd.GeoDataFrame, tasdiffDf = load_tas_diff()):
  if 'tas' in featureDf.columns:
    raise ValueError('tas column already exists in featureDf')
  df = gpd.sjoin_nearest(featureDf.to_crs(epsg=3857), tasdiffDf.to_crs(epsg=3857)).to_crs(epsg=4326)
  from IPython.display import display
  display(df)
  return df['tas']

# joined['tas'] = joined['tas'] * 2/3