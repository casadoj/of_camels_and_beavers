import logging
# import os
from pathlib import Path
import sys
import time
from datetime import datetime
from itertools import product
from typing import Tuple

import numpy as np
import xarray as xr
import zarr
from pyproj import CRS
from tqdm.auto import tqdm
from zarr.codecs import BloscCodec


def _get_dir_size(path):
    """Calculate total size of a directory in GB[cite: 1]."""
    path = Path(path)
    if not path.exists():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / (
        1024**3
    )


def _clean_attrs(attrs: dict) -> dict:
    """Convert numpy types in attributes to standard python types for JSON serialization[cite: 1]."""
    cleaned = {}
    for k, v in attrs.items():
        if isinstance(v, (np.integer, np.floating)):
            cleaned[k] = v.item()
        elif isinstance(v, np.ndarray):
            cleaned[k] = v.tolist()
        else:
            cleaned[k] = v
    return cleaned




def dataset_to_zarr_v3(
    ds: xr.Dataset,
    target_store: str,
    chunks: Tuple[int, int, int],
    shards: Tuple[int, int, int],
    overwrite: bool = True,
) -> None:
    """Saves a pre-computed/pre-processed xarray Dataset to a sharded Zarr V3 store.

    Parameters:
    -----------
    ds: xr.Dataset
        The ready-to-save Dataset containing variables (e.g. precip, avgtemp, etc.).
    target_store: str
        Path for the output Zarr store (e.g. "cerra_daily_iberia.zarr").
    chunks: tuple of 3 ints
        Inner chunk shape (time, lat, lon). Use -1 for full dimension length.
    shards: tuple of 3 ints
        Outer shard shape (time, lat, lon). Use -1 for full dimension length.
    overwrite: bool
        Whether to delete an existing Zarr store at target_store before writing.
    """

    # 1. Setup Logging
    log_file = f"zarrify_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger(__name__)
    start_time = time.time()

    target_store = Path(
        target_store
        if target_store.endswith(".zarr")
        else target_store + ".zarr"
    )
    if overwrite and target_store.exists():
        import shutil

        logger.info(f"Overwriting existing Zarr store at: {target_store}")
        shutil.rmtree(target_store)

    logger.info(f"Starting Zarr v3 conversion to: {target_store}")

    # 2. CRS & Dimension Verification
    for projection in ["wgs_1984", "rotated_pole"]:
        if projection in ds:
            crs = CRS.from_cf(ds[projection].attrs)
            ds = ds.rio.write_crs(crs)
            break

    # define spatial dimensions
    x_dim = next((d for d in ["lon", "longitude", "x", "rlon"] if d in ds.dims), None)
    y_dim = next((d for d in ["lat", "latitude", "y", "rlat"] if d in ds.dims), None)
    if x_dim and y_dim:
        ds = ds.rio.set_spatial_dims(x_dim=x_dim, y_dim=y_dim)
    else:
        logger.warning('Could not automatically determine spatial dimensions.')

    # define temporal dimension
    time_dim = "time" if "time" in ds.dims else "valid_time"

    geo_lat = next((c for c in ["lat", "latitude"] if c in ds.variables), None)
    geo_lon = next((c for c in ["lon", "longitude"] if c in ds.variables), None)

    # Calculate shapes and dynamic chunks/shards
    shape = (
        ds.sizes[time_dim],
        ds.sizes[y_dim],
        ds.sizes[x_dim],
    )  # (time, lat, lon)

    # Resolve -1 dimensions for shards/chunks
    chunks = tuple(int(shape[i] if chunks[i] == -1 else chunks[i]) for i in range(len(chunks)))
    shards = tuple(int(shape[i] if shards[i] == -1 else shards[i]) for i in range(len(shards)))
    logger.info(f"Grid shape: {shape} | Inner Chunks: {chunks} | Shards: {shards}")

    # # Validate chunk/shard dimensions
    # if any(s % c != 0 for s, c in zip(shards, chunks)):
    #     raise ValueError("Shard size should be multiples of the chunk size")

    # 3. Create Zarr V3 Structure
    root = zarr.create_group(target_store, overwrite=True, zarr_format=3)

    if ds.attrs:
        root.attrs.update(_clean_attrs(ds.attrs))

    # Save 1D Coordinate dimensions
    for dim in [time_dim, y_dim, x_dim]:
        if dim and dim in ds.coords and dim not in root:
            data = ds.coords[dim].values
            root.create_array(
                name=dim,
                data=data,
                dimension_names=[dim],
                attributes=_clean_attrs(ds.coords[dim].attrs),
                chunks=(len(data),),
            )

    # Define V3 compressor
    compressor = BloscCodec(cname="zstd", clevel=5, shuffle="bitshuffle")

    # Save 2D Geographic Coordinates (if separate from dimensions)
    spatial_chunks = chunks[1:]
    for geo_coord in [geo_lat, geo_lon]:
        if (
            geo_coord
            and geo_coord in ds
            and geo_coord not in root
            and geo_coord not in [x_dim, y_dim]
        ):
            logger.info(
                f"Saving 2D coordinate array '{geo_coord}' to Zarr root"
            )
            coord_da = ds[geo_coord]
            root.create_array(
                name=geo_coord,
                data=coord_da.values,
                dimension_names=list(coord_da.dims),
                attributes=_clean_attrs(coord_da.attrs),
                chunks=spatial_chunks,
                compressors=[compressor],
            )

    # 4. Process and Write Data Variables
    data_vars = list(ds.data_vars)
    logger.info(f"Variables to write: {data_vars}")

    for var in data_vars:
        da = ds[var].astype("float32")
        var_attrs = _clean_attrs(da.attrs)

        # Save variable
        z_array = root.create_array(
            name=var,
            shape=shape,
            chunks=chunks,
            shards=shards,
            dtype='f4',
            dimension_names=[time_dim, y_dim, x_dim],
            compressors=[compressor],
            attributes=var_attrs,
        )

        # Tiled streaming write per shard tile
        step_time, step_lat, step_lon = shards
        times = range(0, shape[0], step_time)
        lats = range(0, shape[1], step_lat)
        lons = range(0, shape[2], step_lon)
        tiles = list(product(times, lats, lons))
        n_tiles = len(tiles)

        logger.info(f"Writing variable '{var}' across {n_tiles} shard tiles...")
        for time_o, lat_o, lon_o in tqdm(tiles, desc=f"Writing {var}", leave=False):
            time_f = min(time_o + step_time, shape[0])
            lat_f = min(lat_o + step_lat, shape[1])
            lon_f = min(lon_o + step_lon, shape[2])

            try:
                # Load shard slice into RAM
                block = da.isel({
                    time_dim: slice(time_o, time_f),
                    y_dim: slice(lat_o, lat_f),
                    x_dim: slice(lon_o, lon_f),
                }).compute()

                # Write into the Zarr array
                z_array[time_o:time_f, lat_o:lat_f, lon_o:lon_f] = block.values

            except Exception as e:
                logger.error(f"Tile failed -> Var: {var} Time: {time_o} Lat: {lat_o} Lon: {lon_o}: {e}")
                continue

    # 5. Summary Statistics
    duration = (time.time() - start_time) / 60
    final_size_gb = _get_dir_size(target_store)
    logical_size_gb = sum(ds[v].nbytes for v in data_vars) / (1024**3)
    compression_ratio = (logical_size_gb / final_size_gb if final_size_gb > 0 else 0)

    logger.info("--- Conversion Complete ---")
    logger.info(f"Total duration: {duration:.2f} minutes")
    logger.info(f"Final size on disk: {final_size_gb:.2f} GB")
    logger.info(f"Compression ratio: {compression_ratio:.2f}x")