import argparse
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Union, Optional
from tqdm.auto import tqdm
import logging
from datetime import datetime
import geopandas as gpd
import xarray as xr

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'basin-stats_{datetime.now():%Y%m%d%H%M}.log')
    ]
)
logger = logging.getLogger(__name__)


def read_data(
        input_path: Union[str, Path], 
        chunks: Optional[Dict] = None,
        crs: Optional[Union[int, str]] = None
    ) -> xr.Dataset:
    """Reads input maps in either NetCDF or Zarr format.

    Parameters:
    -----------
    input_path: str or pathlib.Path
        Path to the input data. For 'netcdf4', this is a directory containing .nc files.
        For 'zarr', this is the path to the Zarr store directory.
    chunks: dictionary
        Dictionary defining Dask chunks. For NetCDF, defaults to 'auto' if None. For Zarr,
        defaults to the native on-disk chunking if None.
    crs: int or str, optional
        Coordinate reference system to assign to the dataset. If None, EPSG:4326 is assumed.

    Returns:
    --------
    ds: xr.Dataset 
        The loaded dataset with spatial CRS information.
    """

    input_path = Path(input_path)
    if not input_path.is_dir():
        logger.error(f'{input_path} is missing or not a directory!')
        sys.exit(1)
    
    engine = 'zarr' if input_path.suffix == '.zarr' else 'netcdf4'
    if engine == 'netcdf4':
        filepaths = sorted(list(input_path.glob('*.nc')))
        if not filepaths:
            logger.error(f'No NetCDF files found in "{input_path}"')
            sys.exit(2)

        logger.info(f'{len(filepaths)} input NetCDF files found in "{input_path}"')
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
            logger.info(f'MFDataset failed, attempting static load: {e}')
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
    
    # Assign Coordinate Reference System
    ds = ds.rio.write_crs(4326 if crs is None else crs)

    return ds


def read_pixarea(pixarea: Union[str, Path], crs: Optional[Union[int, str]] = None) -> xr.DataArray:
    """It reads the LISFLOOD pixel area static map.
    
    Parameters:
    -----------
    pixarea: string or Path
        a NetCDF file with pixel area used to compute weighted statistics. It is specifically 
        meant for geographic projection systems where the area of a pixel varies with latitude
    crs: int or str, optional
        Coordinate reference system to assign to the dataset. If None, EPSG:4326 is assumed.

    Returns:
    --------
    weight: xr.DataArray
    """

    pixarea = Path(pixarea)
    if not pixarea.is_file():
        logger.error(f'{pixarea} is not a file!')
        sys.exit(1)
    
    try:
        weight = xr.open_dataset(pixarea, engine='netcdf4')['Band1']
    except Exception as e:
        logger.error(f'An error occurred while loading the pixel area map "{pixarea}": {e}')
        sys.exit(2)

    weight = weight.rio.write_crs(4326 if crs is None else crs)

    return weight


def basin_statistics(
        data: Union[xr.DataArray, xr.Dataset],
        basins: gpd.GeoDataFrame,
        statistic: Union[str, List[str]], 
        weight: Optional[xr.DataArray] = None,
        output: Optional[Union[str, Path]] = None,
        overwrite: bool = False,
        decimals: int = 6
    ) -> Optional[xr.Dataset]:
    """
    It computes basin polygon statistics of the input data.
    
    Parameters:
    -----------
    data: xarray.DataArray or xarray.Dataset
        Input data.
    basins: gpd.GeoDataFrame
        The polygons of the basins.
    statistic: string or list of strings
        Statistics to be computed. Only some statistics are available: 'mean', 'sum', 'std', 'var', 'min', 'max', 
        'median', 'count'
    weight: optional or xr.DataArray
        Map used to weight each pixel in "data" before computing the statistics. It is meant to take into account 
        the different pixel area in geographic projections.
    output: optional, str or pathlib.Path
        Directory where the resulting Parquet files will be saved. If not provided, the results are returned as a 
        xr.Dataset.
    overwrite: boolean
        Whether to overwrite or skip basins whose output file already exists. By default is False, so the 
        basin will be skipped.
    
    Returns:
    --------
    A xr.Dataset of all basin statistics or a parquet file for each basin in the "output" directory.
    """

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

    # ensure CRS matches
    if basins.crs != data.rio.crs:
        basins = basins.to_crs(data.rio.crs)

    # add weight to 'data'
    if weight is not None:
        if weight.rio.crs != data.rio.crs:
            weight = weight.rio.reproject(data.rio.crs)
        data = data.assign(weight=weight)

    # process basins
    for ID in tqdm(basins.index, desc='basins'):
        
        if output is not None:
            # fileout = output / f'{ID:04}.nc'
            fileout = output / f'{ID:04}.parquet'
            if fileout.exists() and  not overwrite:
                logger.info(f'Output file {fileout} already exists. Moving forward to the next basin')
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
    logger.info(f"Time elapsed: {elapsed_time:0.2f} seconds")

    if output is None:
        results = xr.concat(results, dim='id')
        return results
    

def main(argv=sys.argv):
    prog = os.path.basename(argv[0])
    parser = argparse.ArgumentParser(
        description="""
        Utility to compute basin statistics from (multiple) NetCDF files or a Zarr store.
        Basin polygons are required to define the areas of interest.
        The area map is optional and accounts for varying pixel area with latitude.
        """,
        prog=prog,
    )
    parser.add_argument("-b", "--basins", required=True, 
                        help="Polygon shapefile of the basins.")
    parser.add_argument("-i", "--input", required=True, 
                        help="Directory containing the input files: either NetCDF files or a Zarr store.")
    parser.add_argument("-s", "--statistics", nargs='+', required=True, 
                        help='List of statistics to be computed. Possible values: mean, sum, std, var, min, max, median, count')
    parser.add_argument("-o", "--output", required=True, 
                        help="Directory where the output files will be saved")
    parser.add_argument("-a", "--area", required=False, default=None, 
                        help="NetCDF file of pixel area used to weigh the statistics")
    parser.add_argument("-c", "--chunks", type=int, nargs=3, required=False, default=None,
                        help="Dask chunk size (time, lat, lon). Defaults to 'auto' for NetCDF and native chunking for Zarr.")
    parser.add_argument("-d", "--decimals", type=int, required=False, default=6,
                        help="Number of decimals to keep in the results.")
    parser.add_argument("-w", "--overwrite", action="store_true", 
                        help="Overwrite existing output files")
    args = parser.parse_args()

    success = False

    try:
        logger.info('Reading input data...')
        if args.chunks is not None:
            chunks = {'time': args.chunks[0], 'lat': args.chunks[1], 'lon': args.chunks[2]}
        else:
            chunks = None
        data = read_data(args.input, chunks=chunks)

        logger.info('Reading basin polygons...')
        basins = gpd.read_file(args.basins)
        basins.set_index(basins.columns[0], inplace=True)

        logger.info('Reading pixel area map (if provided)...')
        weight = read_pixarea(args.area) if args.area is not None else None

        logger.info('Computing basin statistics...')
        basin_statistics(
            data, 
            basins, 
            args.statistics, 
            weight=weight, 
            output=args.output, 
            overwrite=args.overwrite, 
            decimals=args.decimals
        )

        logger.info('Process completed successfully.')
        success = True
    
    except FileNotFoundError as e:
        logger.error(f"A required file was not found: {e}")
    except OSError as e:
        logger.error(f"An I/O error occurred: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    
    if not success:
        sys.exit(1)


def main_script():
    sys.exit(main())


if __name__ == "__main__":
    main_script()