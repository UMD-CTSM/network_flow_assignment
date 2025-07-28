import numpy as np
import netCDF4
from datetime import datetime
import cftime
import urllib.request
import pathlib

def download_files( save_path='Data/spear' ):
    spear_ensembles = (
        "r10i1p1f1",
        "r11i1p1f1",
        "r12i1p1f1",
        "r13i1p1f1",
        "r14i1p1f1",
        "r15i1p1f1",
        "r16i1p1f1",
        "r17i1p1f1",
        "r18i1p1f1",
        "r19i1p1f1",
        "r1i1p1f1",
        "r20i1p1f1",
        "r21i1p1f1",
        "r22i1p1f1",
        "r23i1p1f1",
        "r24i1p1f1",
        "r25i1p1f1",
        "r26i1p1f1",
        "r27i1p1f1",
        "r28i1p1f1",
        "r29i1p1f1",
        "r2i1p1f1",  # Note: 'r2i1ip1f1' is a typo in the original code, corrected to 'r2i1p1f1'
        "r30i1p1f1",
        "r3i1p1f1",
        "r4i1p1f1",
        "r5i1p1f1",
        "r6i1p1f1",
        "r7i1p1f1",
        "r8i1p1f1",
        "r9i1p1f1"
    )

    spear_sources = (
        ('historical', '192101-201412'),
        ('scenarioSSP5-85', '201501-210012')
    )

    spear_variable = 'tas'
    spear_variable_cat = 'Amon'

    spear_BASE_URL = 'https://noaa-gfdl-spear-large-ensembles-pds.s3.amazonaws.com/SPEAR/GFDL-LARGE-ENSEMBLES/CMIP/NOAA-GFDL/GFDL-SPEAR-MED'
    for member in spear_ensembles:
        for source, dates in spear_sources:
            print(f'starting {member}/{source}')
            # tas_Amon_GFDL-SPEAR-MED_scenarioSSP5-85_r11i1p1f1_gr3_201501-210012.nc
            filename = f'{spear_variable}_{spear_variable_cat}_GFDL-SPEAR-MED_{source}_{member}_gr3_{dates}.nc'
            if source=='historical' and member=='r2i1p1f1': realmember = 'r2i1ip1f1'
            else: realmember = member
            filepath = f'{spear_BASE_URL}/{source}/{realmember}/{spear_variable_cat}/{spear_variable}/gr3/v20210201/{filename}'
            saveloc = pathlib.Path.cwd() / save_path / source
            print(filepath)
            saveloc.mkdir(parents=True, exist_ok=True)
            local_filename = urllib.request.urlretrieve(filepath, saveloc / filename)

# download_files('inputs/spear')

def process_tas(basePath = pathlib.Path.cwd() / 'inputs' / 'spear', processFn = lambda x :np.array(x).mean(0).mean(0) ):

    (basePath / 'scenarioSSP5-85').mkdir(parents=True, exist_ok=True)
    (basePath / 'historical').mkdir(parents=True, exist_ok=True)
    proj_tas_datasets = [netCDF4.Dataset(d) for d in (basePath / 'scenarioSSP5-85').iterdir()]
    print(proj_tas_datasets[0]['time'].units)
    hist_tas_datasets = [netCDF4.Dataset(d) for d in (basePath / 'historical').iterdir()]

    cnvD = lambda d, x, y, z=1: cftime.date2num(datetime(x,y,z),units=d['time'].units,calendar=d['time'].calendar)
    timeSelect = lambda data, y1, y2 : (data['time'] > cnvD(data, y1, 1)) & (data['time'] < cnvD(data, y2, 12, 31))
    recBet = lambda data, y1, y2 : data['tas'][timeSelect(data, y1, y2)]
    
    proj_tas_list = [recBet(proj_tas, 2091, 2100) for proj_tas in proj_tas_datasets]
    print(len(proj_tas_list), 'proj tas datasets')
    return proj_tas_list
    hist_tas_list = [recBet(hist_tas, 2001, 2010) for hist_tas in hist_tas_datasets]
    return proj_tas_list, hist_tas_list
    proj_tas = processFn(proj_tas_list)
    hist_tas = processFn(hist_tas_list)

    sample_tas_data = proj_tas_datasets[0]
    with netCDF4.Dataset(basePath.parent / "spear_tas_proj.nc", "w", format="NETCDF4") as grp:
        grp.createDimension('lon', len(sample_tas_data['lon']))
        grp.createDimension('lat', len(sample_tas_data['lat']))

        grp.createVariable('lon', sample_tas_data['lon'].datatype, ('lon'))
        grp['lon'][:] = sample_tas_data['lon'][:]
        grp['lon'].setncatts(sample_tas_data['lon'].__dict__)
        grp.createVariable('lat', sample_tas_data['lat'].datatype, ('lat'))
        grp['lat'].setncatts(sample_tas_data['lat'].__dict__)
        grp['lat'][:] = sample_tas_data['lat'][:]
        grp.createVariable('tas', sample_tas_data['tas'].datatype, ('lat', 'lon'))
        grp['tas'].setncatts(sample_tas_data['tas'].__dict__)
        grp['tas'][:] = proj_tas
        
        
    with netCDF4.Dataset(basePath.parent / "spear_tas_hist.nc", "w", format="NETCDF4") as grp:
        grp.createDimension('lon', len(sample_tas_data['lon']))
        grp.createDimension('lat', len(sample_tas_data['lat']))

        grp.createVariable('lon', sample_tas_data['lon'].datatype, ('lon'))
        grp['lon'][:] = sample_tas_data['lon'][:]
        grp['lon'].setncatts(sample_tas_data['lon'].__dict__)
        grp.createVariable('lat', sample_tas_data['lat'].datatype, ('lat'))
        grp['lat'].setncatts(sample_tas_data['lat'].__dict__)
        grp['lat'][:] = sample_tas_data['lat'][:]
        grp.createVariable('tas', sample_tas_data['tas'].datatype, ('lat', 'lon'))
        grp['tas'].setncatts(sample_tas_data['tas'].__dict__)
        grp['tas'][:] = hist_tas
    
    # tas_data = proj_tas - hist_tas
    # with netCDF4.Dataset(basePath.parent / "spear_tas_diff.nc", "w", format="NETCDF4") as grp:
    #     grp.createDimension('lon', len(sample_tas_data['lon']))
    #     grp.createDimension('lat', len(sample_tas_data['lat']))

    #     grp.createVariable('lon', sample_tas_data['lon'].datatype, ('lon'))
    #     grp['lon'][:] = sample_tas_data['lon'][:]
    #     grp['lon'].setncatts(sample_tas_data['lon'].__dict__)
    #     grp.createVariable('lat', sample_tas_data['lat'].datatype, ('lat'))
    #     grp['lat'].setncatts(sample_tas_data['lat'].__dict__)
    #     grp['lat'][:] = sample_tas_data['lat'][:]
    #     grp.createVariable('tas', sample_tas_data['tas'].datatype, ('lat', 'lon'))
    #     grp['tas'].setncatts(sample_tas_data['tas'].__dict__)
    #     grp['tas'][:] = tas_data