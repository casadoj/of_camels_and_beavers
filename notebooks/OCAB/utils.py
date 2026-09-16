import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
import rioxarray as rxr


def merge_points(ls: list[gpd.GeoDataFrame | pd.DataFrame], keep='dam'):

    # merge input DataFrames
    points = pd.concat(ls, axis=0)

    # in case of duplicates, keep only the selected kind
    duplicates = points.geometry.duplicated(keep=False)
    if duplicates.sum() > 0:
        points = pd.concat([
            points[~duplicates],
            points[duplicates].xs(keep, level='kind', drop_level=False)
        ], axis=0).sort_index()

    return points


def np2xr(
        data: np.ndarray,
        template: xr.DataArray,
        mask: None | np.ndarray,
        name: None | str,
        attrs: None | dict
) -> xr.DataArray:
    """
    """

    da = xr.DataArray(
        data=data,
        dims=['y', 'x'],
        coords={'y': template.y, 'x': template.x}
    )
    if mask is not None:
        da = da.where(mask)

    if name is not None:
        da = da.rename(name)

    if attrs is not None:
        da.attrs.update(attrs)

    # set spatial reference
    da.rio.write_crs(template.rio.crs, inplace=True)
    da.rio.write_nodata(np.nan, inplace=True)

    return da