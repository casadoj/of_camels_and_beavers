"""
Copyright 2019-2023 European Union
Licensed under the EUPL, Version 1.2 or as soon they will be approved by the European Commission  subsequent versions of the EUPL (the "Licence");
You may not use this work except in compliance with the Licence.
You may obtain a copy of the Licence at:
https://joinup.ec.europa.eu/sites/default/files/inline-files/EUPL%20v1_2%20EN(1).txt
Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the Licence for the specific language governing permissions and limitations under the Licence.
"""

import argparse
import os
from pathlib import Path
# import pandas as pd
import sys
import time
import geopandas as gpd
import xarray as xr
from typing import Dict, List, Literal, Union, Optional
from tqdm.auto import tqdm


def read_data(
        input_path: Union[str, Path], 
        engine: Literal['netcdf4', 'zarr'],
        chunks: Optional[dict] = None
    ) -> xr.Dataset:
    """Reads input maps in either NetCDF or Zarr format.

    Parameters:
    -----------
    input_path: str or pathlib.Path
        Path to the input data. For 'netcdf4', this is a directory containing .nc files.
        For 'zarr', this is the path to the Zarr store directory.
    engine: str
        The format of the input data: 'netcdf4' or 'zarr'.
    chunks: dictionary
        Dictionary defining Dask chunks. For NetCDF, defaults to 'auto' if None. For Zarr,
        defaults to the native on-disk chunking if None.

    Returns:
    --------
    ds: xr.Dataset 
        The loaded dataset with spatial CRS information.
    """

    input_path = Path(input_path)
    if not input_path.is_dir():
        print(f'ERROR: {input_path} is missing or not a directory!')
        sys.exit(1)
        
    if engine == 'netcdf4':
        filepaths = sorted(list(input_path.glob('*.nc')))
        if not filepaths:
            print(f'ERROR: No NetCDF files found in "{input_path}"')
            sys.exit(2)

        print(f'{len(filepaths)} input NetCDF files found in "{input_path}"')
        try:
            # for dynamic maps
            ds = xr.open_mfdataset(
                filepaths, 
                chunks='auto' if chunks is None else chunks, 
                parallel=False, # it was True before
                coords='minimal',
                data_vars='minimal',
                compat='override',
                engine='netcdf4'
                ).astype('float32')
        except:
            # for static maps
            ds = xr.Dataset({
                file.stem.split('_')[0]: xr.open_dataset(file, engine='netcdf4')['Band1'] 
                for file in filepaths
            })
    
    elif engine == 'zarr':
        ds = xr.open_dataset(
            input_path, 
            engine='zarr', 
            zarr_format=3, 
            chunks={} if chunks is None else chunks, 
            consolidated=False
        )

    if 'wgs_1984' in ds:
        ds = ds.drop_vars('wgs_1984')
        ds = ds.rio.write_crs(4326)

    return ds

# def read_masks(mask: Union[str, Path]) -> Dict[int, xr.DataArray]:
#     """It loads the catchment masks in NetCDF format from the input directory

#     Parameters:
#     -----------
#     mask: str or pathlib.Path
#         directory that contains the NetCDF files that define the catchment boundaries. 
#         These files can be the output of the `cutmaps` tool

#     Returns:
#     --------
#     masks: dictionary of xr.DataArray
#         keys represent the catchment ID and the values boolean maps of the catchment
#     """

#     # check masks
#     mask = Path(mask)
#     if not mask.is_dir():
#         print(f'ERROR: {mask} is not a directory!')
#         sys.exit(1)

#     maskpaths = list(mask.glob('*.nc'))
#     if not maskpaths:
#         print(f'ERROR: No NetCDF files found in "{mask}"')
#         sys.exit(2)
        
#     print(f'{len(maskpaths)} mask NetCDF files found in "{mask}"')

#     # load masks
#     masks = {}
#     for maskpath in maskpaths:  
#         ID = int(maskpath.stem)
#         try:
#             try:
#                 aoi = xr.open_dataset(maskpath, engine='netcdf4')['Band1']
#             except:
#                 aoi = xr.open_dataarray(maskpath, engine='netcdf4')
#             aoi = xr.where(aoi.notnull(), 1, aoi)
#             masks[ID] = aoi
#         except Exception as e:
#             print(f'ERROR: The mask {maskpath} could not be read: {e}')
#             continue

#     return masks

def read_pixarea(pixarea: Union[str, Path]) -> xr.DataArray:
    """It reads the LISFLOOD pixel area static map.
    
    Parameters:
    -----------
    pixarea: string or Path
        a NetCDF file with pixel area used to compute weighted statistics. It is specifically 
        meant for geographic projection systems where the area of a pixel varies with latitude

    Returns:
    --------
    weight: xr.DataArray
    """

    pixarea = Path(pixarea)
    if not pixarea.is_file():
        print(f'ERROR: {pixarea} is not a file!')
        sys.exit(1)
    
    try:
        weight = xr.open_dataset(pixarea, engine='netcdf4')['Band1']
    except Exception as e:
        print(f'ERROR: The weighing map "{pixarea}" could not be loaded: {e}')
        sys.exit(2)

    return weight

def catchment_statistics(
        data: Union[xr.DataArray, xr.Dataset],
        basins: gpd.GeoDataFrame,
        statistic: Union[str, List[str]], 
        weight: Optional[xr.DataArray] = None,
        output: Optional[Union[str, Path]] = None,
        overwrite: bool = False,
        decimals: int = 6
    ) -> Optional[xr.Dataset]:

    start_time = time.perf_counter()

    if isinstance(data, xr.DataArray):
        data = xr.Dataset({data.name: data})

    # check statistic
    if isinstance(statistic, str):
        statistic = [statistic]
    possible_stats = ['mean', 'sum', 'std', 'var', 'min', 'max', 'median', 'count']
    assert all(stat in possible_stats for stat in statistic), "All values in 'statistic' should be one of these: {0}".format(', '.join(possible_stats))
    stats_dict = {var: statistic for var in data}

    # output directory
    if output is None:
        results = []
    else:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)

    # define spatial dimensions
    x_dim = next((d for d in ['lon', 'longitude', 'x'] if d in data.dims), 'x')
    y_dim = next((d for d in ['lat', 'latitude', 'y'] if d in data.dims), 'y')
    data = data.rio.set_spatial_dims(x_dim=x_dim, y_dim=y_dim)
    if weight is not None:
        weight = weight.rio.set_spatial_dims(x_dim=x_dim, y_dim=y_dim)

    # ansure CRS matches
    if basins.crs != data.rio.crs:
        basins = basins.to_crs(data.rio.crs)

    # add weight to 'data'
    if weight is not None:
        data = data.assign(weight=weight)

    # process basins
    for ID in tqdm(basins.index, desc='Basins'):
        
        if output is not None:
            # fileout = output / f'{ID:04}.nc'
            fileout = output / f'{ID:04}.parquet'
            if fileout.exists() and  not overwrite:
                print(f'Output file {fileout} already exists. Moving forward to the next catchment')
                continue

        # extract basin polygon and its bounding box
        polygon = basins.loc[[ID]].geometry

        # clip data to the basin polygon
        basin_data = data.rio.clip(polygon, drop=True, all_touched=True)

        # compute statistics
        stats_results = {}
        for var, stats in stats_dict.items():

            if weight is not None:
                weighted_data = basin_data[var].weighted(basin_data['weight'].fillna(0))
            
            for stat in stats:
                use_weight = weight is not None and stat in ['mean', 'sum', 'std', 'var']
                calc_data = weighted_data if use_weight else basin_data[var]
                x = getattr(calc_data, stat)(dim=[x_dim, y_dim])
                stats_results[f'{var}_{stat}'] = x.expand_dims(id=[ID])

        data_basin = xr.Dataset(stats_results).compute()

        # save results
        if output is None:
            results.append(data_basin)
        else:
            # data_basin.to_netcdf(fileout)
            df = data_basin.to_dataframe()
            df.drop(['crs', 'spatial_ref', 'wgs_1984', 'id'], axis=1, errors='ignore', inplace=True)
            df.round(decimals).to_parquet(fileout)

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Time elapsed: {elapsed_time:0.2f} seconds")

    if output is None:
        results = xr.concat(results, dim='id')
        return results
    
def main(argv=sys.argv):
    prog = os.path.basename(argv[0])
    parser = argparse.ArgumentParser(
        description="""
        Utility to compute catchment statistics from (multiple) NetCDF files.
        The mask masp are NetCDF files with values in the area of interest and NaN elsewhere.
        The area map is optional and accounts for varying pixel area with latitude.
        """,
        prog=prog,
    )
    parser.add_argument("-i", "--input", required=True, 
                        help="Directory containing the input files: either NetCDF files or a Zarr store.")
    parser.add_argument("-c", "--catchment", required=True, 
                        help="Polygon shapefile of the catchments.")
    parser.add_argument("-s", "--statistic", nargs='+', required=True, 
                        help='List of statistics to be computed. Possible values: mean, sum, std, var, min, max, median, count')
    parser.add_argument("-o", "--output", required=True, 
                        help="Directory where the output files will be saved")
    parser.add_argument("-a", "--area", required=False, default=None, 
                        help="NetCDF file of pixel area used to weigh the statistics")
    parser.add_argument("-w", "--overwrite", action="store_true", 
                        help="Overwrite existing output files")
    parser.add_argument("-d", "--decimals", required=False, default=6,
                        help="Number of decimals to keep in the results.")
    
    args = parser.parse_args()

    try:
        data = read_data(args.input)
        catchments = gpd.read_file(args.catchment)
        catchments.set_index(catchmnegs.columns[0], inplace=True)
        weight = read_pixarea(args.area) if args.area is not None else None
        catchment_statistics(data, catchments, args.statistic, weight=weight, output=args.output, overwrite=args.overwrite, decimals=args.decimals)
    except Exception as e:
        print(f'ERROR: {e}')
        sys.exit(1)
    
def main_script():
    sys.exit(main())

if __name__ == "__main__":
    main_script()
