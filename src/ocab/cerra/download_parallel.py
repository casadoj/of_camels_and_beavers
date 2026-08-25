import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import tempfile

import cdsapi
import numpy as np
from tqdm.auto import tqdm
import xarray as xr
import xesmf as xe


# variable attributes
VARIABLES = {
    'tp': {
        'dataset': 'reanalysis-cerra-land',
        'request': {
            'variable': ['total_precipitation'],
            'level_type': ['surface'],
            'product_type': ['analysis'],
            'year': ['2000'],
            'month': [f'{month:02}' for month in range(1, 13)],
            'day': [f'{day:02}' for day in range(1, 32)],
            'time': ['06:00'],
            'data_format': 'netcdf',
        },
        'regridding_method': 'bilinear',
    },
    't2m': {
        'dataset': 'reanalysis-cerra-single-levels',
        'request': {
            "variable": ['2m_temperature'],
            "level_type": "surface_or_atmosphere",
            "data_type": ["reanalysis"],
            "product_type": "analysis",
            "year": ['2000'],
            "month": [f"{m:02d}" for m in range(1, 13)],
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": [f'{hour:02}:00' for hour in range(0, 24, 3)],
            "data_format": "netcdf",
        },
        'regridding_method': 'bilinear',
    }
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Download CERRA/CERRA-Land data from CDS in parallel."
    )
    parser.add_argument('-p', '--path', type=str, required=True, help='Base path to save data.')
    parser.add_argument('-v', '--var', type=str, required=True, choices=['tp', 't2m'], help='Variable name.')
    parser.add_argument('-s', '--start', type=int, default=1984, help='Start year.')
    parser.add_argument('-e', '--end', type=int, default=datetime.now().year - 1, help='End year.')
    parser.add_argument('-a', '--area', nargs=4, type=float, default=None, help='N, W, S, E extent.')
    parser.add_argument('-r', '--resolution', type=float, default=0.05, help='Target resolution (deg).')
    parser.add_argument('-w', '--workers', type=int, default=4, help='Number of parallel downloads.')
    return parser.parse_args()

def process_year(year, args, path_out, target, weights_file, encoding):
    """Downloads and processes one year of data."""

    # define output file
    out_file = path_out / f'{args.var}_{year}.nc'
    if out_file.is_file():
        return f'Skipped {year} (already exists)'

    # extract variable configuration
    cfg = VARIABLES[args.var]
    dataset = cfg['dataset']
    request = cfg['request'].copy()
    request.update({'year': [str(year)]})
    method = cfg['regridding_method']

    # independent client for each thread
    client = cdsapi.Client(timeout=600)

    if args.area is None:
        # download complete file
        client.retrieve(dataset, request).download(out_file)
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            # download complete file to temporal storage
            temp_file = Path(tmpdir) / f'{args.var}_{year}.nc'
            client.retrieve(dataset, request).download(temp_file)

            # open temporal dataset
            with xr.open_dataset(temp_file) as ds:
                ds = ds.rename({"valid_time": "time", "latitude": "lat", "longitude": "lon"})

                # Carga los pesos ya precalculados para evitar conflictos de hilos
                regridder = xe.Regridder(
                    ds, 
                    target, 
                    method=method, 
                    periodic=False,
                    filename=weights_file,
                    reuse_weights=True,
                )

                # regrid and define projection
                ds_regrid = regridder(ds)
                ds_regrid = (
                    ds_regrid
                    .rio.set_spatial_dims(x_dim='lon', y_dim='lat')
                    .rio.write_crs("EPSG:4326")
                )

                # save
                ds_regrid.to_netcdf(out_file, encoding=encoding)

    return f'Finished {year}'

def prepare_weights_file(args, path_out, target):
    """Descarga un año de muestra si es necesario para generar el archivo de pesos de xESMF."""

    # extract variable configuration
    cfg = VARIABLES[args.var]
    method = cfg['regridding_method']

    # define file name
    weights_file = path_out.parent / f'weights_{args.var}_{args.resolution:.2f}_{method}.nc'

    if weights_file.exists():
        return weights_file
    print("Generating xESMF weights file before parallel processing...")

    # initialize client
    client = cdsapi.Client(timeout=600)
    
    # download one timestep to define weights
    sample_request = cfg['request'].copy()
    sample_request.update({
        'year': [str(args.start)],
        'month': ['01'],
        'day': ['01'],
        'time': ['06:00'] if args.var == 'tp' else ['00:00']
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        # download temporary file
        temp_file = Path(tmpdir) / "sample.nc"
        client.retrieve(cfg['dataset'], sample_request).download(temp_file)

        # load sample and produce weights
        with xr.open_dataset(temp_file) as ds:
            ds = ds.rename({"valid_time": "time", "latitude": "lat", "longitude": "lon"})
            regridder = xe.Regridder(ds, target, method=method, periodic=False)
            regridder.to_netcdf(weights_file)

    print(f"Weights saved to {weights_file}")
    return weights_file

def main():

    # parse arguments
    args = parse_args()

    # define output path
    path_out = Path(args.path) / args.var
    path_out.mkdir(parents=True, exist_ok=True)

    target = None
    weights_file = None
    if args.area is not None:
        # create output grid
        lat_max, lon_min, lat_min, lon_max = args.area
        target = xr.Dataset(
            coords={
                "lat": np.arange(lat_min, lat_max + args.resolution / 2, args.resolution),
                "lon": np.arange(lon_min, lon_max + args.resolution / 2, args.resolution),
            }
        )
        # generate weights file
        weights_file = prepare_weights_file(args, path_out, target)

    encoding = {
        args.var: {
            "zlib": True,
            "complevel": 1,
            "shuffle": True,
        }
    }

    years = list(range(args.start, args.end + 1))

    # parallel execution using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                process_year, year, args, path_out, target, weights_file, encoding
            ): year
            for year in years
        }

        for future in tqdm(as_completed(futures), total=len(years), desc='Progress'):
            try:
                result = future.result()
            except Exception as exc:
                year = futures[future]
                print(f'Year {year} generated an exception: {exc}')

if __name__ == "__main__":
    main()