from typing import Dict, Literal, List, Optional, Union
from pathlib import Path
from tqdm.auto import tqdm
import logging

logger = logging.getLogger(__name__)

import pandas as pd


def read_attributes(
    path: Union[str, Path],
    ID: Optional[List] = None,
    index_col: Optional[str] = 'id'
) -> pd.DataFrame:
    """It reads all the attribute tables from the specified dataset and, if provided, applies filters.
    
    Parameters:
    -----------
    path: string or pathlib.Path
        Directory where the dataset is stored
    ID: list (optional)
        List of the IDs of interest
    index_col: string (optional)
        Name of the column to be used as index
        
    Returns:
    --------
    attributes: pandas.DataFrame
        Concatenation of all the attributes in the dataset
    """      
        
    # import all tables of attributes
    try:
        attributes = pd.concat(
            [pd.read_csv(file, index_col=index_col) for file in path.glob('*.csv')],
            axis=1,
            join='outer'
        )
        attributes.index.name = index_col
        if ID is not None:
            if isinstance(ID, list) is False:
                ID = [ID]
            attributes = attributes.loc[ID]
    except Exception as e:
        raise ValueError(f'ERROR while reading attribute tables from directory {path}: {e}') from e
        
    return attributes


def read_timeseries(
    path: Union[str, Path],
    ID: Optional[List[int]] = None,
    periods: Optional[Dict[int, Dict[str, pd.Timestamp]]] = None,
    variables: Optional[List[str]] = None,
    format: Literal['parquet', 'csv'] = 'parquet'
) -> Dict[int, pd.DataFrame]:
    """It reads the time series in the dataset and saves them in a dictionary.
    
    Parameters:
    -----------
    path: string or pathlib.Path
        Directory where the dataset is stored
    ID: list (optional)
        List of the IDs of interest
    periods: dictionary (optional)
        If provided, it cuts the time series to the specified period. It is a dictionary of dictionaries, where 
        the keys are the ID, and the values are dictionaries with two entries ('start' and 'end') that contain 
        timestamps of the selected beginning and end of the study period
    variables: list (optional)
        List of the variables of interest
    format: string
        File format in which the time series are stored: 'parquet' (default) or 'csv'
    
    Returns:
    --------
    timeseries: dictionary
        It contains the timeseries of the selected IDs as pandas.DataFrame
    """

    if ID is None:
        ID = [int(file.stem) for file in path.glob(f'*.{format}')]
    elif isinstance(ID, list) is False:
        ID = [ID]

    # if variables is None:
    #     variables = ['inflow', 'storage', 'outflow', 'elevation']

    # read time series
    timeseries = {}
    for ID in tqdm(ID, leave=False):
        # read time series
        file = path / f'{ID}.{format}'
        try:
            if format == 'csv':
                ts = pd.read_csv(file)
                ts['date'] = pd.to_datetime(ts['date'])
                ts = ts.set_index('date').sort_index().asfreq('D')
            elif format == 'parquet':
                ts = pd.read_parquet(file)
            else:
                raise ValueError(f'"format" must be either "parquet" or "csv. {format} was provided')
        except (FileNotFoundError, Exception) as e:
            logger.error(f"Failed to process {file}: {e}")
            continue

        # select study period
        try:
            if periods is not None:
                start, end = [periods[str(ID)][f'{x}_dates'][0] for x in ['start', 'end']]
                ts = ts.loc[start:end, :]
        except Exception as e:
            logger.error(f'While trimming to the study period the time series for ID {ID}:\n{e}')

        # select varibles
        try:
            if variables is not None:
                missing_vars = set(variables).difference(ts.columns)
                if len(missing_vars) > 0:
                    logger.warning(f'Time series for ID {ID} is missing variables: {missing_vars}')
                ts = ts[ts.columns.intersection(variables)]
            # convert storage variables to m3
            ts.iloc[:, ts.columns.str.contains('storage')] *= 1e6
        except Exception as e:
            logger.error(f'While selecting variables from the time series for ID {ID}:\n{e}')

        # save time series
        try:
            timeseries[ID] = ts
        except Exception as e:
            logger.error(f'Time series for ID {ID} could not be saved:\n{e}')
        
    return timeseries