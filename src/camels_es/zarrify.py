import argparse
import logging
import time
import shutil
from datetime import datetime
import os
from pathlib import Path
from tqdm.auto import tqdm
import sys
import numpy as np
import xarray as xr
import zarr
from zarr.codecs import BloscCodec
from typing import Tuple, Optional, Literal, Union
from itertools import product

def _get_dir_size(path):
    """Calculate total size of a directory in GB."""
    path = Path(path)
    if not path.exists():
        return 0
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file()) / (1024**3)

def _clean_attrs(attrs: dict) -> dict:
    """Convert numpy types in attributes to standard python types for JSON serialization."""
    cleaned = {}
    for k, v in attrs.items():
        if isinstance(v, (np.integer, np.floating)):
            cleaned[k] = v.item()
        elif isinstance(v, np.ndarray):
            cleaned[k] = v.tolist()
        else:
            cleaned[k] = v
    return cleaned

def nc_to_zarr(
    input_path: str,
    target_store: str,
    chunks: Tuple[int, int, int],
    shards: Tuple[int, int, int],
    resample: Optional[str] = None,
    variable: Optional[Literal[str]] = None
) -> None:
    """Converts the NetCDF files in the input path to a sharded Zarr V3 store at the target location
    with the specified chunk and shard sizes, and optional resampling to daily frequency.
    
    Parameters:
    -----------
    input_path: str
        Path where the input NetCDF files are located.
    target_store: str
        Path and name of the output Zarr store (extension needed).
    chunks: tuple of 3 ints
        Chunk shape as 3 integers: time, lat, lon. Use -1 for full length of that dimension.
    shards: tuple of 3 ints
        Shard shape as 3 integers: time, lat, lon. Use -1 for full length of that dimension.
    resample: str (optional)
        Aggregation method used when resampling to daily frequency: 'mean', 'max', 'min', 'sum'.
    """
    # 1. Setup Logging
    log_file = "zarrify_{}.log".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    start_time = time.time()

    logger.info(f"Starting conversion. Input: {input_path}, Output: {target_store}")
    
    # 2. Read data
    try:
        ds = xr.open_mfdataset(
            input_path,
            engine='netcdf4',
            # parallel=True,
            chunks={'time': 365}
            ).astype('float32')
        
        # define variable to extract
        variables = list(ds.data_vars)
        if variable:
            if variable not in variables:
                raise ValueError(f"Variable '{variable}' not found. Options: {list(variables)}")
        else:
            if len(variables) != 1:
                raise ValueError(f"Expected one variable in the dataset, found: {variables}")
            variable = variables[0]

        da = ds[variable]

        if len(chunks) != da.ndim:
            raise ValueError("Chunks must match the dataset dimensions")
        if len(shards) != da.ndim:
            raise ValueError("Shards must match the dataset dimensions")

        if resample:
            logger.info(f"Resampling '{variable}' to '{resample}' daily values")
            da = getattr(da.resample(time="1D"), resample)()

        logical_size_gb = da.nbytes / (1024**3)
        logger.info(f"Dataset loaded. Logical size: {logical_size_gb:.2f} GB")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return
    
    # get shape and correct chunks and shards (handle -1 as full length)
    shape = da.shape
    chunks = tuple(int(shape[i] if chunks[i] == -1 else chunks[i]) for i in range(len(chunks)))
    shards = tuple(int(shape[i] if shards[i] == -1 else shards[i]) for i in range(len(shards)))
    logger.info(f"Grid shape: {shape} | Chunks: {chunks} | Shards: {shards}")
    # Validate chunk/shard dimensions
    if any(s % c != 0 for s, c in zip(shards, chunks)):
        raise ValueError("Shard size should be multiples of the chunk size")

    # 3. Create Zarr V3 Structure
    if os.path.isdir(target_store):
        root = zarr.open_group(target_store, mode='a', zarr_format=3)
    else:
        root = zarr.create_group(target_store, overwrite=True, zarr_format=3)
    if ds.attrs:
        root.attrs.update(_clean_attrs(ds.attrs))

    # Save coordinates only if they don't exist
    for dim in da.dims:
        if dim not in root:
            data = da.coords[dim].data
            root.create_array(
                name=dim,
                data=data,
                dimension_names=[dim],
                attributes=_clean_attrs(da[dim].attrs),
                chunks=(len(data),)
            )

    # Define V3 compressor
    compressor = BloscCodec(cname='zstd', clevel=5, shuffle='bitshuffle')
    z_array = root.create_array(
        name=variable,
        shape=shape,
        chunks=chunks,
        shards=shards,
        dtype='f4',
        dimension_names=list(da.dims),
        compressors=[compressor],
        attributes=_clean_attrs(da.attrs)
    )

    # 4. Tiled streaming write
    time_dim, lat_dim, lon_dim = da.dims
    step_time, step_lat, step_lon = shards
    times = range(0, shape[0], step_time)
    lats = range(0, shape[1], step_lat)
    lons = range(0, shape[2], step_lon)
    tiles = product(times, lats, lons)
    n_tiles = len(times) * len(lats) * len(lons)
    logger.info(f"Processing data in {n_tiles} spatial tiles")
    for time_o, lat_o, lon_o in tqdm(tiles, total=n_tiles, desc="Tiles"):
        time_f = min(time_o + step_time, shape[0])
        lat_f = min(lat_o + step_lat, shape[1])
        lon_f = min(lon_o + step_lon, shape[2])

        try:
            # load the block into memory
            block = da.isel({
                time_dim: slice(time_o, time_f),
                lat_dim: slice(lat_o, lat_f),
                lon_dim: slice(lon_o, lon_f)
            }).compute()

            # Write into the Zarr array
            z_array[time_o:time_f, lat_o:lat_f, lon_o:lon_f] = block.values

        except Exception as e:
            logger.error(f"Tile failed -> Lat: {lat_o} Lon: {lon_o}: {e}")
            continue

    # 5. Final Stats
    duration = (time.time() - start_time) / 60
    final_size_gb = _get_dir_size(target_store)
    compression_ratio = logical_size_gb / final_size_gb if final_size_gb > 0 else 0

    logger.info("--- Conversion Complete ---")
    logger.info(f"Total duration: {duration:.2f} minutes")
    logger.info(f"Final size on disk: {final_size_gb:.2f} GB")
    logger.info(f"Compression ratio: {compression_ratio:.2f}x")

    ds.close()

def main():
    parser = argparse.ArgumentParser(
        description="Convert NetCDF files to a sharded Zarr V3 store."
    )
    parser.add_argument("-i", "--input", type=str, required=True, 
                        help="Input path (use quotes if using wildcards)")
    parser.add_argument("-o", "--output", type=str, required=True, 
                        help="Output Zarr store path")
    parser.add_argument("-v", "--variable", type=str, 
                        help="Specify the variable to be extracted, if the NetCDF files contain multiple variables.")
    parser.add_argument("-c", "--chunks", type=int, nargs=3, default=[-1, 20, 20],
                        help="Chunking (time, lat, lon). Default: -1 20 20")
    parser.add_argument("-s", "--shards", type=int, nargs=3, default=[-1, 100, 100],
                        help="Sharding (time, lat, lon). Default: -1 100 100")
    parser.add_argument("-r", "--resample", type=str, choices=['mean', 'max', 'min', 'sum'],
                        help="Resample to daily frequency using the specified statistic (e.g., mean, sum)")
    parser.add_argument('-w', '--overwrite', action='store_true',
                        help="Delete the existing Zarr store")
    args = parser.parse_args()

    # Path cleaning
    input_path = os.path.join(args.input, '*.nc') if os.path.isdir(args.input) else args.input
    target_store = args.output if args.output.endswith('.zarr') else args.output + '.zarr'
    if args.overwrite and os.path.isdir(target_store):
        shutil.rmtree(target_store)

    # Run conversion
    nc_to_zarr(
        input_path=input_path, 
        target_store=target_store, 
        chunks=tuple(args.chunks), 
        shards=tuple(args.shards), 
        resample=args.resample,
        variable=args.variable
        )

if __name__ == "__main__":
    main()