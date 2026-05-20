import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, Tuple


def resample_daily(
        df: pd.DataFrame, 
        decimals: int = 3
    ) -> pd.DataFrame:
    """Resample hourly time series to daily"""

    df = df.resample('D').mean().round(decimals)
    df.index = df.index.normalize()
    df.index.name = 'date'

    return df


def compute_filling(df: pd.DataFrame, capacity: float) -> pd.DataFrame:
    """Computes reservoir filling out of storage and total capacity"""
    
    if 'storage' in df.columns:
        df['filling'] = df['storage'] / capacity

    return df


def define_observed_period(
        timeseries: Dict[int, pd.DataFrame], 
        last_year: Optional[int] = None
    ) -> (pd.DataFrame):
    """Defines start and end year of the time series, and whether the station is active or not

    Parameters:
    -----------
    timeseries: dictionary
        A dictionary where keys are station IDs and values the observed time series
    last_year: integer
        Last recorded year. Used to define whether the station is active or not
    """

    if last_year is None:
        last_year = datetime.now().year
    df = pd.DataFrame(index=timeseries.keys(), columns=['start', 'end', 'active'], dtype='Int64')
    for ID, ts in timeseries.items():
        start, end = ts.index.min(), ts.index.max()
        df.loc[ID, 'start'] = start.year
        df.loc[ID, 'end'] = end.year if end.year < last_year else np.nan
        df.loc[ID, 'active'] = 1 if end.year == last_year else 0

    return df


def time_encoding(
    time: np.ndarray,
    period: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Transforms time feature values in an xarray.DataArray to sine and cosine components.

    Parameters:
    -----------
    time: xarray.DataArray
        An xarray.DataArray with time feature values (e.g., month, day of year).
    period: integer
        The period of the time feature (e.g., 12 for months, 7 for days of the week).

    Returns:
    --------
    sin_da, cos_da (tuple of xarray.DataArray):
        Sine and cosine transformations of the time feature values.
    """
    
    # Normalize time feature values to [0, 2π]
    if time.min() == 1:
        norm_da = (time - 1) * 2 * np.pi / period
    elif time.min() == 0:
        norm_da = time * 2 * np.pi / period
    else:
        norm_da = (time - 1) * 2 * np.pi / period
        
    # correct leap years, if necessary
    norm_da = norm_da.where(norm_da <= np.pi * 2, np.pi * 2)
    
    return np.round(np.sin(norm_da), 8), np.round(np.cos(norm_da), 8)