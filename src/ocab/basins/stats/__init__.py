from pathlib import Path
from typing import List
import xarray as xr

from .main import read_data, read_pixarea, basin_statistics


# @casadoj: this is an old function to load data, but the one needed for the
#           EFAS static maps
def read_input_maps(
        path: Path,
        variables: List[str],
        crs: int = None
):
    """
    Read and combine multiple NetCDF files into a single xarray Dataset.

    Loads spatial variables from a directory where files follow the naming 
    convention '{variable}_*.nc'. It attempts to extract data from a 
    variable named 'Band1' first, falling back to the variable's own name 
    if 'Band1' is missing.

    Parameters
    ----------
    path : pathlib.Path
        The directory containing the '.nc' files.
    variables : list of str
        A list of variable names to look for and load.
    crs : int, optional
        The EPSG code for the Coordinate Reference System. If None (default), 
        it defaults to EPSG:4326.

    Returns
    -------
    ds : xarray.Dataset
        A consolidated dataset containing all requested variables, 
        with unnecessary spatial metadata coordinates removed and 
        the CRS explicitly assigned.

    Notes
    -----
    The function uses ``xr.open_mfdataset`` to handle cases where a single 
    variable is split across multiple files. It performs a ``.compute()`` 
    call immediately, loading the data from Dask into memory.
    """

    # load maps
    try:
        ds = xr.Dataset({var: xr.open_mfdataset(f'{path}/{var}_*.nc')['Band1'].compute() for var in variables})
    except:
        ds = xr.Dataset({var: xr.open_mfdataset(f'{path}/{var}_*.nc')[var].compute() for var in variables})

    # remove unnecessary variables
    for var in ['crs', 'spatial_ref', 'wgs_1984']:
        if var in ds:
            ds = ds.drop(var)
    
    # Assign Coordinate Reference System
    ds = ds.rio.write_crs(4326 if crs is None else crs)

    return ds