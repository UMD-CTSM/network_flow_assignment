from pathlib import Path
import geopandas as gpd
import pandas as pd
import netCDF4
import xarray as xr
from shapely import ops
import numpy as np

# basePath = Path.cwd().parent / 'inputs'
# diffNcPath = basePath / 'spear_tas_diff.nc'


def load_tas_diff(path):
  tasDiffdf = xr.open_dataset(path).to_dataframe()
  # tasDiffdf.index.names =['geo_center_x_zone', 'geo_center_y_zone']
  tasDiffdf = tasDiffdf.reset_index()
  tasDiffdf.loc[tasDiffdf.lon > 180, 'lon'] = tasDiffdf.lon -360
  tasDiffdf = gpd.GeoDataFrame(
    tasDiffdf, geometry=gpd.points_from_xy(tasDiffdf.lon, tasDiffdf.lat), crs="epsg:4326"
  )

  return tasDiffdf
  
def load_tas_nparr(path):
  tasDiffnp = np.load(path)
  # print(tasDiffnp.mean().mean())
  lat_dim, lon_dim = tasDiffnp.shape
  lats = np.linspace(-90, 90, lat_dim)
  lons = np.linspace(0, 360, lon_dim)
  lat_grid, lon_grid = np.meshgrid(lats, lons, indexing='ij')
  tasDiffdf = pd.DataFrame({
    'lat': lat_grid.flatten(),
    'lon': lon_grid.flatten(),
    'tas': tasDiffnp.flatten()
  })
  # Assume you have separate arrays for lat and lon, e.g., tasDiffdf_lat, tasDiffdf_lon
  # If not, you need to load or compute them accordingly and add as columns:
  # tasDiffdf['lat'] = tasDiffdf_lat
  # tasDiffdf['lon'] = tasDiffdf_lon
  tasDiffdf.loc[tasDiffdf.lon > 180, 'lon'] = tasDiffdf.lon -360
  tasDiffdf = gpd.GeoDataFrame(
    tasDiffdf, geometry=gpd.points_from_xy(tasDiffdf.lon, tasDiffdf.lat), crs="epsg:4326"
  )

  return tasDiffdf

def join_tas_diff(featureDf : gpd.GeoDataFrame, tasdiffDf):
  # if 'tas' in featureDf.columns:
  #   raise ValueError('tas column already exists in featureDf')
  df = gpd.sjoin_nearest(featureDf.to_crs(epsg=3857), tasdiffDf.to_crs(epsg=3857)).to_crs(epsg=4326)
  return df['tas']

# joined['tas'] = joined['tas'] * 2/3