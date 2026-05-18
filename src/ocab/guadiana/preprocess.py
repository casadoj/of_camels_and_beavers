from typing import Dict
from pathlib import Path
from tqdm.auto import tqdm

import pandas as pd


from typing import Dict


def _read_csv(file: Path) -> pd.DataFrame:
    """Reads the raw CSV file and preprocesses it to extract the relevant information."""

    # read data
    data = pd.read_csv(
        file, 
        sep=';', 
        parse_dates=['fecha'], 
        dayfirst=False
    )

    # rename columns
    rename_cols = {
        'fecha': 'date',
        'valor': 'value'
    }
    data.rename(columns=rename_cols, inplace=True)

    # extract ID and variable
    cod_variable = data['cod_variable'].str.split('/', expand=True)
    cod_variable.columns = ['ID', 'variable']
    data = cod_variable.join(data.drop(columns=['cod_variable']))

    return data


def _extract_timeseries(
        df: pd.DataFrame,
        freq: str = 'D'
    ) -> pd.DataFrame:
    """Pivots the raw data to create a time series dataframe with the specified frequency.
    
    Parameters:
    -----------
    df: pandas.DataFrame
        The raw dataframe containing the date, variable, and value columns.
    freq: str
        The frequency of the time series used to ensure completeness. Default is 'D' for daily.

    Returns:
    --------
    pandas.DataFrame
        A dataframe with the date as the index and the variables as columns.
    """

    # remove duplicates
    df = df.drop_duplicates(subset=['date', 'variable'], keep='first')

    # pivot table
    ts = df[['date', 'variable', 'value']].pivot(
        index='date',
        columns='variable',
        values='value'
    )
    ts.rename_axis(None, axis=1, inplace=True)
    ts.index = pd.to_datetime(ts.index)

    # rename columns
    # @casadoj: in some cases, there are multiple values of stage or dicharge.
    #           I use those indicated by them via mail.
    rename_cols = {
        'NR1': 'stage',
        'QR1': 'discharge',
        'NE1': 'level',
        'VE1': 'volume',
        'QSR': 'outflow'
    }
    cols = ts.columns.intersection(rename_cols.keys())
    ts = ts[cols].rename(columns=rename_cols, errors='ignore')
    
    return ts.asfreq(freq)


def get_timeseries(file: Path) -> Dict[str, pd.DataFrame]:
    """Read station data from a file."""

    # read data
    data = _read_csv(file)

    # reorganize by ID
    timeseries = {}
    for ID in tqdm(data['ID'].unique()):
        df = data[data['ID'] == ID].drop(columns='ID')
        ts = _extract_timeseries(df)
        timeseries[ID] = ts

    return timeseries
