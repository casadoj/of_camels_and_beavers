import pandas as pd
from typing import List
from pathlib import Path
import pickle

from ocab.config import Config


def create_sample_file(cfg: Config, sample: List, file: Path):
    """Creates the TXT file that lists the basin IDs.
    
    Parameters:
    -----------
    cfg: Config
        Dataset configuration file
    sample: List
        List of basin IDs
    file: pathlib.Path
        TXT file
    """

    file = Path(file)
    if file.suffix != '.txt':
        raise ValueError('"file" must have be a text file (extension ".txt")')
    with open(file, 'w') as f:
        for ID in sample:
            key = f'{cfg.prefix}_{ID}' if cfg.prefix is not None else ID
            f.write(f'{key}\n')


def create_period_file(cfg: Config, sample: List, form: pd.DataFrame, file: Path):
    """Creates the Pickle file that defines the observed period.
    
    Parameters:
    -----------
    cfg: Config
        Dataset configuration file
    sample: List
        List of basin IDs
    form: pandas.DataFrame
        Table of answers to the public questionnaire. It must include the columns "start_dates"
        and "end_dates"
    file: pathlib.Path
        TXT file
    """

    # create dictionary of selected periods
    periods = {}
    for ID in sample:
        key = f'{cfg.prefix}_{ID}' if cfg.prefix is not None else ID
        periods[key] = {col: form.loc[ID, col].to_list() for col in ['start_dates', 'end_dates']}

    # export Pickle file
    file = Path(file)
    if file.suffix != '.pkl':
        raise ValueError('"file" must have be a Pickle file (extension ".pkl")')
    with open(file, 'wb') as f:
        pickle.dump(periods, f)