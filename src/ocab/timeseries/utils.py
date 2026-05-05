import pandas as pd


def resample_daily(
        df: pd.DataFrame, 
        decimals: int = 3
    ) -> pd.DataFrame:
    """Resample hourly time series to daily"""

    df = df.resample('D').mean().round(decimals)
    df.index = df.index.date
    df.index.name = 'date'

    return df


def compute_filling(df: pd.DataFrame, capacity: float) -> pd.DataFrame:
    """Computes reservoir filling out of storage and total capacity"""
    
    if 'storage' in df.columns:
        df['filling'] = df['storage'] / capacity

    return df