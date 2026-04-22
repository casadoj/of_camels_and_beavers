import pandas as pd

aggregation = {
    'temp_degC': 'mean',
    'precip_mm': 'sum',
    'pet_mm': 'sum',
    'discharge_mm': 'sum',
}

def compute_monthly_climatology(timeseries: pd.DataFrame) -> pd.DataFrame:
    """Creates a monthly climatology by resampling the daily data and then averaging across months."""

    agg_logic = {var: func for var, func in aggregation.items() if var in timeseries.columns}
    if len(agg_logic) == 0:
        raise ValueError("No variables in the timeseries match the aggregation logic.")
    
    timeseries_monthly = timeseries.resample('MS').agg(agg_logic)
    return timeseries_monthly.groupby(timeseries_monthly.index.month).mean()


def compute_annual_timeseries(timeseries: pd.DataFrame) -> pd.DataFrame:
    """Creates the annual time series by resampling the daily data."""

    agg_logic = {var: func for var, func in aggregation.items() if var in timeseries.columns}
    if len(agg_logic) == 0:
        raise ValueError("No variables in the timeseries match the aggregation logic.")
    
    return timeseries.resample('YS').agg(agg_logic)