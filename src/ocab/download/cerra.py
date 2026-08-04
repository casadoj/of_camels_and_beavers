from datetime import datetime
from pathlib import Path
import tempfile
import argparse

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
        'regridding_method': 'conservative',
    },
    '2t': {
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
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description=
            """Download CERRA or CERRA-Land data from the CopernicusClimate Data Store.
            The original data is in Lambert Conformal Conic projection and covers all Europe.
            If the '--area' option is specified, the data will be regridded to a regular lat/lon 
            grid (projection EPSG:4326) with the specified extent.
            """
    )
    parser.add_argument(
        '-p',
        '--path',
        type=str,
        required=True,
        help='Base path where the data will be saved.'
    )
    parser.add_argument(
        '-v',
        '--var',
        type=str,
        required=True,
        choices=['tp', '2t'],
        help=(
            "Variable to be downloaded: "
            "'tp'   total precipitation (kg/m2), "
            "'2t' 2m temperature (K)"
        )
    )
    parser.add_argument(
        '-s',
        '--start',
        type=int,
        default=1984,
        help='Start year for data download.'
    )
    parser.add_argument(
        '-e',
        '--end',
        type=int,
        default=datetime.now().year - 1,
        help='End year for data download.'
    )
    parser.add_argument(
        '-a',
        '--area',
        nargs=4,
        type=float,
        default=None,
        help='Area of interest: N, W, S, E (default: Europe).'
    )
    parser.add_argument(
        '-r',
        '--resolution',
        type=float,
        default=0.05,
        help='Resolution of the output grid in degrees (default: 0.05).'
    )
    return parser.parse_args()

def main():

    args = parse_args()

    # output path
    path_out = Path(args.path) / args.var
    path_out.mkdir(parents=True, exist_ok=True)

    if args.area is not None:
        # output grid
        lat_max, lon_min, lat_min, lon_max = args.area
        target = xr.Dataset(
            coords={
                "lat": np.arange(lat_min, lat_max + args.resolution / 2, args.resolution),
                "lon": np.arange(lon_min, lon_max + args.resolution / 2, args.resolution),
            }
        )

        # ouput NetCDF compression
        encoding = {
            args.var: {
                "zlib": True,
                "complevel": 1,
                "shuffle": True,
            }
        }

    # extract variable configuration
    cfg = VARIABLES[args.var]
    dataset = cfg['dataset']
    request = cfg['request'].copy()
    regridder = None
    method = cfg['regridding_method']

    # Loop through years to download data
    client = cdsapi.Client(timeout=600) # Initialize the client
    for year in tqdm(range(args.start, args.end + 1), desc='Year'):
            
        # define output file
        out_file = path_out / f'{args.var}_{year}.nc'
        if out_file.is_file():
            print(f'File {out_file} already exists, skipping.')
            continue

        # update year in the request
        request.update({'year': [str(year)]})
            
        if args.area is None:
            # download complete file
            client.retrieve(dataset, request).download(out_file)
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                    
                # download complete file to temporal storage
                temp_file = Path(tmpdir) / f'{args.var}_{year}.nc'
                client.retrieve(dataset, request).download(temp_file)
        
                # open dataset
                with xr.open_dataset(temp_file) as ds:
                    ds = ds.rename({"latitude": "lat", "longitude": "lon"})
        
                    # define regridder
                    if regridder is None:
                        weights_file = path_out / f'weights_{args.var}_{args.resolution:.2f}_{method}.nc'
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
        
        print(f'Saved file: {out_file}')

if __name__ == "__main__":
    main()