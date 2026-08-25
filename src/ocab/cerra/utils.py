from typing import Literal, Dict, Optional

import xarray as xr

def read_cerra(
        paths, 
        var: Literal['tp', 't2m'], 
        chunks: Optional[Dict] = None
    ) -> xr.Dataset:
    """Reads the NetCDF files of the CERRA(Land) dataset already clipped to the
    area of interest and reprojected to EPSG:4326
    
    Parameters
    ----------
    paths:
    var:
    chunks:

    Returns
    -------
    xr.Dataset
    """
    
    # read data
    ds = xr.open_mfdataset(
        paths=paths,
        combine='by_coords',
        data_vars='all',
    ).unify_chunks()

    # adapt variable units
    if var == 'tp':
        ds[var].attrs["units"] = "mm/d"
        ds[var].attrs["long_name"] = "total precipitation"
    elif var == 't2m':
        ds[var] = ds[var] - 273.15
        ds[var].attrs['units'] = 'degC'
        ds[var].attrs['long_name'] = 'temperature at 2 m'
        # ds = ds.rename_vars({'t2m': 'temperature'})
    else:
        raise ValueError(f'"var" must be either "tp" (total precipitation) or "t2m" (2 meter temperature)')
    
    # adapt temporal dimension: name and resolution
    if 'valid_time' in ds.dims or 'valid_time' in ds.coords:
        ds = ds.rename({'valid_time': 'time'})
    ds_daily = ds[var].resample(time='1D')
    if var == 'tp':
        ds = xr.Dataset({'totprec': ds_daily.sum()})
    elif var == 't2m':
        ds = xr.Dataset({
            'avgtemp': ds_daily.mean(),
            'maxtemp': ds_daily.max(),
            'mintemp': ds_daily.min(),
        })
        ds['avgtemp']['long_name'] = 'temperature at 2 m: daily mean'
        ds['maxtemp']['long_name'] = 'temperature at 2 m: daily maximum'
        ds['mintemp']['long_name'] = 'temperature at 2 m: daily minimum'

    # drop unnecessary coordinates
    if 'expver' in ds.coords:
        ds = ds.drop_vars('expver')

    # rechunk
    if chunks is not None:
        ds = ds.chunk(chunks)

    # define projection
    ds['lat'].attrs['units'] = 'degrees_north'
    ds['lon'].attrs['units'] = 'degrees_east'
    ds = ds.rio.write_crs('EPSG:4326')
    ds = ds.rio.set_spatial_dims(x_dim='lon', y_dim='lat')
        
    return ds