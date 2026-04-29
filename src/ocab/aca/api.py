import pandas as pd
import geopandas as gpd
from typing import Dict
from pathlib import Path

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

import logging
logger = logging.getLogger(__name__)


def _read_excel(file: Path) -> pd.DataFrame:

    data = pd.read_excel(
        file,
        sheet_name="Quantitat d'aigua disponible",
        skiprows=7,
        usecols=range(1, 9),
        engine='openpyxl'
    )

    # rename columns
    rename_cols = {
        'Data': 'date',
        'Estació': 'name',
        'Conca': 'system',
        'UTM X': 'x_etrs89',
        'UTM Y': 'y_etrs89',
        'Variable': 'signal',
        'Mitjana': 'average',
        'Unitat Mesura': 'unit'
    }
    data = data[rename_cols.keys()].rename(columns=rename_cols)

    return data


def _extract_signals(signals: pd.Series) -> pd.DataFrame:
    """
    Parse hydrological signal strings to extract station IDs, names, 
    river context, and variable types.

    This function processes raw signal strings (e.g., 'EA001_Llobregat_Cabal Riu Llobregat')
    and maps them to a structured DataFrame. It uses a dictionary-based 
    mapping strategy on unique values to optimize performance for large datasets.

    Parameters
    ----------
    signals : pd.Series
        A series of strings containing the raw signal data to be parsed. 
        Strings are expected to follow a pattern containing an ID, 
        a station name, and a descriptor (e.g., 'cabal riu', 'cabal total').

    Returns
    -------
    pd.DataFrame
        A DataFrame with the same index as the input `signals`, containing 
        the following columns:
        - 'id_saih': The uppercase unique identifier for the station.
        - 'name': The title-cased name of the measurement station.
        - 'river': The title-cased name of the water body, or None.
        - 'variable': The standardized variable name ('discharge' or 'outflow').
    """

    # rename variables
    rename_vars = {
        'cabal desguas': 'outflow',
        'cabal llavi assut': 'overflow',
        'cabal riu': 'discharge',
        'cabal riera': 'discharge',
        'cabal total': 'total_discharge',
        'cabal sortida': 'outflow',
    }

    # define mapping of the signals and attributes
    mapping = {}
    for signal in signals.unique():
        ls = signal.lower().split('_')
        if 'cabal desguas' in signal.lower():
            var = 'cabal desguas'
            ID, name = ls[0], ls[1]
            river = None 
        elif 'cabal llavi assut' in signal.lower():
            var = 'cabal llavi assut'
            ID, name = ls[0], ls[1]
            river = None
        elif 'cabal riu' in signal.lower():
            var = 'cabal riu'
            ID, name = ls[0], ls[1]
            river = signal.lower().split('cabal riu')[-1].strip().replace('_', ' ')
        elif 'cabal riera' in signal.lower():
            var = 'cabal riera'
            ID, name = ls[0], ls[1]
            river = signal.lower().split('cabal riera')[-1].strip().replace('_', ' ')
        elif 'cabal sortida' in signal.lower():
            var = 'cabal sortida'
            ID = ls[0]
            if len(ls) == 3:
                name = ls[1]
            elif len(ls) == 4:
                name = ls[2]
            river = None
        elif 'cabal total' in signal.lower():
            var = 'cabal total'
            if len(ls) == 3:
                ID, name = ls[0], ls[1]
                river = ls[2].removeprefix('cabal total').strip()
            elif len(ls) == 4:
                ID = '_'.join(ls[:2]) # keep only the ID of the gauge station (remove channel ID)
                name = ls[2]
                river = ls[3].removeprefix('cabal total').strip()
            elif len(ls) == 5:
                ID = '_'.join(ls[:3])
                name = ls[3]
                river = ls[4].removeprefix('cabal total').strip()
        else:
            logger.warning(f'Variable not found in signal: "{signal}"')
            ID, name = ls[0], ls[1]
            river, var = None, None
        mapping[signal] = {
            'id_saih': ID.upper(),
            'name': name.title(),
            'river': river.title() if river is not None else None,
            'variable': rename_vars[var] if var is not None else None
        }

    mapped_data = [mapping[s] for s in signals]
    return pd.DataFrame(mapped_data, index=signals.index)


def _extract_timeseries(df: pd.DataFrame) -> pd.DataFrame:

    # remove duplicates
    df = df.drop_duplicates(subset=['date', 'variable'], keep='first')

    # pivot table
    ts = df[['date', 'variable', 'average']].pivot(
        index='date',
        columns='variable',
        values='average'
    )
    ts.rename_axis(None, axis=1, inplace=True)
    ts.index = pd.to_datetime(ts.index)
    
    return ts.asfreq('D')


def _create_geodataframe(
        attributes: pd.DataFrame,
        epsg: int = 4326
    ) -> gpd.GeoDataFrame:

    attributes = gpd.GeoDataFrame(
        attributes,
        geometry=gpd.points_from_xy(attributes.x_etrs89, attributes.y_etrs89),
        crs=25831
    )
    if epsg != 25831:
        attributes = attributes.to_crs(epsg)
        if epsg == 4326:
            attributes['lon_wgs84'] = attributes.geometry.x
            attributes['lat_wgs84'] = attributes.geometry.x
            cols = [col for col in attributes.columns if col != 'geometry'] + ['geometry']
            attributes = attributes[cols]

    return attributes


def get_station_data(
        file: Path, 
        epsg: int = 4326
    ) -> (gpd.GeoDataFrame, Dict[str, pd.DataFrame]):
    """
    Parse gauging stations data from the Catalan Water Agency (ACA) Excel exports.

    This function processes Excel files containing water availability data, 
    extracting time-series for variables (discharge, outflow) and 
    generating a spatial GeoDataFrame of station locations.

    Parameters
    ----------
    file : Path
        Path to the Excel file exported from the ACA portal. Expected to 
        contain a sheet named "Quantitat d'aigua disponible".
    epsg : int, default 4326
        The Coordinate Reference System (CRS) to return the GeoDataFrame in. 
        Input data is assumed to be in ETRS89 / UTM zone 31N (EPSG:25831).

    Returns
    -------
    attributes : gpd.GeoDataFrame
        A GeoDataFrame containing the metadata for each station, including 
        name, basin, river, and geometry. If `epsg=4326`, 'lon_wgs84' and 
        'lat_wgs84' columns are appended.
    timeseries : dict of str: pd.DataFrame
        A dictionary where keys are the ACA station IDs and values are 
        Pandas DataFrames containing the pivoted time-series data (discharge
        or outlfow) indexed by date.
    """  

    # load data
    data = _read_excel(file)

    # extract attributes from signals
    attrs = _extract_signals(data['signal'])
    data = pd.concat([data.drop(columns=['signal', 'name']), attrs], axis=1)

    # set index
    data.set_index('id_saih', inplace=True)
    data = data[data.index.notnull()]

    # reorganize by ID
    cols = ['name', 'river', 'system', 'x_etrs89', 'y_etrs89']
    attributes = pd.DataFrame(index=data.index.unique(), columns=cols)
    timeseries = {}
    for ID in attributes.index:
        df = data.loc[[ID]].copy()
        
        # extract station attributes
        attributes.loc[ID, cols] = df.iloc[0][cols].values

        # extract timeseries
        timeseries[ID] = _extract_timeseries(df)

    # convert attributes to geopandas
    attributes = _create_geodataframe(attributes, epsg)
    
    # check dtype
    for col in ['name', 'river', 'system']:
        attributes[col] = attributes[col].str.title()

    return attributes, timeseries


def get_reservoir_data(
        file: Path, 
        epsg: int = 4326
    ) -> (gpd.GeoDataFrame, Dict[str, pd.DataFrame]):
    """
    Parse reservoir data from the Catalan Water Agency (ACA) Excel exports.

    This function processes Excel files containing water availability data, 
    extracting time-series for variables (level, storage, filling) and 
    generating a spatial GeoDataFrame of reservoir locations.

    Parameters
    ----------
    file : Path
        Path to the Excel file exported from the ACA portal. Expected to 
        contain a sheet named "Quantitat d'aigua disponible".
    epsg : int, default 4326
        The Coordinate Reference System (CRS) to return the GeoDataFrame in. 
        Input data is assumed to be in ETRS89 / UTM zone 31N (EPSG:25831).

    Returns
    -------
    reservoirs : gpd.GeoDataFrame
        A GeoDataFrame containing the metadata for each reservoir, including 
        name, basin, and geometry. If `epsg=4326`, 'lon_wgs84' and 
        'lat_wgs84' columns are appended.
    timeseries : dict of str: pd.DataFrame
        A dictionary where keys are the ACA reservoir IDs and values are 
        Pandas DataFrames containing the pivoted time-series data (level, 
        storage, and filling percentage) indexed by date.
    """

    # load data
    data = _read_excel(file)

    # create index with the reservoir ID
    data['id_saih'] = [var.split('_')[0] for var in data['signal']]
    data.set_index('id_saih', inplace=True)

    # simplify station names
    rename_reservoirs = {name: ' '.join(name.upper().split('(')[0].split(' ')[2:]).strip() for name in data['name'].unique()}
    data['name'] = data['name'].map(rename_reservoirs)

    # rename variable
    rename_vars = {
        'Nivell embassament': 'level',
        'Percentatge volum embassat': 'filling',
        'Volum embassament': 'storage',
        'Volum embassat': 'storage'
    }
    data['variable'] = [rename_vars[var.split('_')[-1].split('(')[0].strip()] for var in data['signal']]

    # reorganize by ID
    cols = ['name', 'system', 'x_etrs89', 'y_etrs89']
    attributes = pd.DataFrame(index=data.index.unique(), columns=cols)
    timeseries = {}
    for ID in attributes.index:
        df = data.loc[[ID]].copy()
        
        # extract station attributes
        attributes.loc[ID, cols] = df.iloc[0][cols].values
        
        # extract timeseries
        ts = _extract_timeseries(df)

        # convert filling to the range 0-1
        if 'filling' in ts.columns:
            ts['filling'] /= 100

        # save time series
        timeseries[ID] = ts

        # reservoir capacity (hm3)
        if all([var in ts.columns for var in ['filling', 'storage']]):
            mask = ts[['filling', 'storage']].notnull().all(axis=1)
            capacity = (ts.loc[mask, 'storage'] / ts.loc[mask, 'filling']).round(1).unique()
            if len(capacity) == 1:
                attributes.loc[ID, 'cap_mcm'] = capacity.item()
            elif len(capacity) > 1:
                attributes.loc[ID, 'cap_mcm'] = capacity[0]

    # convert attributes to geopandas
    attributes = _create_geodataframe(attributes, epsg)

    # check dtype
    for col in ['name', 'system']:
        attributes[col] = attributes[col].str.title()

    return attributes, timeseries