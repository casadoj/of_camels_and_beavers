from typing import Dict, List
from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd
import geopandas as gpd


def remove_accents(input_str):
    nfd_form = unicodedata.normalize('NFD', input_str)
    return "".join([c for c in nfd_form if unicodedata.category(c) != 'Mn'])


def extract_gauge_location_river(series: pd.Series) -> (pd.Series, pd.Series):
    """
    It extracts the location and river names from a series of strings.

    Parameters:
    -----------
    series: pd.Series
        Texts that contain the gauge location and rivers

    Returns:
    --------
    names: pd.Series
        Location of the station
    rivers: pd.Series
        River in which the station is located
    """

    # 1. Pre-process: lowercase and remove accents
    clean_text = series.astype(str).str.lower().apply(remove_accents)

    # 2. Define extraction logic using regex or str methods
    rivers = pd.Series(index=series.index, dtype=object)
    names = pd.Series(index=series.index, dtype=object)

    # Case: "rio x (nombre)"
    mask_paren = clean_text.str.contains(r'\(', na=False)
    parts = clean_text[mask_paren].str.split(r'\(', expand=True)
    rivers.loc[mask_paren] = parts[0].str.replace('rio', '', case=False).str.strip()
    names.loc[mask_paren] = parts[1].str.replace(')', '', regex=False).str.strip()

    # Case: "rio x en nombre"
    mask_en = (~mask_paren) & clean_text.str.contains(' en ', na=False)
    parts_en = clean_text[mask_en].str.split(' en ', expand=True)
    rivers.loc[mask_en] = parts_en[0].str.strip()
    names.loc[mask_en] = parts_en[1].str.strip()

    # Case: Starts with 'rio' or 'arroyo' (no extra name)
    mask_prefix = (~mask_paren) & (~mask_en) & clean_text.str.match(r'^(rio|arroyo)', na=False)
    rivers.loc[mask_prefix] = clean_text[mask_prefix].str.replace(r'^(rio|arroyo)', '', regex=True).str.strip()
    
    # Case: Default (Everything else is a name)
    mask_else = rivers.isna()
    names.loc[mask_else] = clean_text[mask_else]

    # 3. Final cleanup: Title Case
    return names.str.title(), rivers.str.title()


def get_stations_hidrosur(file: Path, epsg: int = 4326) -> gpd.GeoDataFrame:
    """
    Import and clean station metadata from a CSV file.

    This function reads a CSV containing station information, standardizes 
    column names from Spanish to English, cleans station names, translates 
    station types, and converts measurement availability into boolean values. 
    The resulting DataFrame is converted to a GeoDataFrame with the specified 
    Coordinate Reference System (CRS).

    Parameters
    ----------
    file : Path
        Path to the CSV file containing the station metadata.
    epsg : int, optional
        The EPSG code for the desired output coordinate system. 
        Defaults to 4326 (WGS 84).

    Returns
    -------
    pd.DataFrame
        A GeoDataFrame containing the cleaned station data, indexed by 'id_saih'.
        If EPSG 4326 is used, 'lon_wgs84' and 'lat_wgs84' columns are added.
    """

    # import station metadata
    stations = pd.read_csv(file)
    stations.columns = stations.columns.str.lower()

    # rename columns
    rename_cols = {
        'número': 'id_saih', 
        'nombre': 'name',
        'provincia': 'province', 
        'tipo de estaciones': 'type', 
        'tipo': 'type', 
        'x (etrs89)': 'x_etrs89',
        'x': 'x_etrs89',
        'y (etrs89)': 'y_etrs89', 
        'y': 'y_etrs89',
        'z (m)': 'z_masl', 
        'temperatura': 'temperature', 
        'pluviometría': 'precipitation', 
        'nivometría': 'snow',
        'humedad': 'humidity', 
        'presión atm.': 'pressure', 
        'vel. viento': 'wind_speed', 
        'dir. viento': 'wind_dir', 
        'rad.solar': 'radiation'
    }
    # stations = stations[stations.columns.intersection(rename_cols)].rename(columns=rename_cols)
    stations = stations[stations.columns.intersection(rename_cols)].rename(columns=rename_cols)
    stations.set_index('id_saih', drop=True, inplace=True)

    # rename stations
    stations.name = [name[:-5] for name in stations.name]
    # correct reservoir names
    names = []
    for name in stations.name:
        # remove string 'embalse' from name
        name = re.sub(r'EMBALSE DE\s+', '', name)
        name = re.sub(r'EMBALSE DEL\s+', 'EL ', name)
        name = re.sub(r'EMBALSE\s+', '', name)
        names.append(name.lower())
    stations['name'] = names
    stations['province'] = stations['province'].str.title()

    # translate station type
    stations['type'] = stations['type'].replace({
        'PLUVIOMÉTRICA': 'pluviometer',
        'AFORO': 'gauge',
        'METEOROLÓGICA': 'meteo',
        'DISTRIBUCIÓN': 'supply',
        'EMBALSE': 'reservoir'
        }
    )

    # convert fields representing variable to boolean
    variables = ['temperature', 'precipitation', 'snow', 'humidity', 'pressure', 'wind_speed', 'wind_dir', 'radiation']
    for var in variables:
        if var in stations.columns:
            stations[var] = stations[var].replace({var[0].upper(): True, ' ': False, 'nan': np.nan})

    # covert to GeoDataFrame
    stations = gpd.GeoDataFrame(
        stations, 
        geometry=gpd.points_from_xy(stations['x_etrs89'], stations['y_etrs89']), 
        crs=25830
    )
    if epsg != 25830:
        stations = stations.to_crs(epsg)
        if epsg == 4326:
            stations['lon_wgs84'] = stations.geometry.x
            stations['lat_wgs84'] = stations.geometry.x
            cols = [col for col in stations.columns if col != 'geometry'] + ['geometry']
            stations = stations[cols]
    
    return stations


def get_timeseries_hidrosur(
        file: Path, 
        freq: str = 'h', 
        tz: str = 'UTC'
        ) -> Dict[int, pd.DataFrame]:
    """Read time series data from the raw TXT file.
    
    Parameters:
    -----------
    file: str or Path
        TXT file containing the time series
    freq: str
        Temporal frequency of the data. By default is hourly: 'h'
    tz: str
        Time zone. By default 'UTC'

    Returns:
    --------
    Dict[int, pd.DataFrame]
        A dictionary where keys are station IDs and values are cleaned DataFrames.
    """

    rename_cols = {
        'estacion': 'id_saih',
        'sensor': 'sensor',
        'fecha': 'datetime',
        'nivel (m)': 'stage',
        'nivel (msnm)': 'level',
        'caudal (m3/s)': 'discharge',
        'volumen (hm3)': 'storage'
    }

    # load time series and rename columns
    data = pd.read_csv(file)
    data.columns = data.columns.str.lower()
    data = data[data.columns.intersection(rename_cols)].rename(columns=rename_cols)

    # convert to datetime
    data['datetime'] = pd.to_datetime(data['datetime']).dt.tz_localize(tz)

    # reorganize the data
    timeseries = {
        ID: group.set_index('datetime')
                    .drop(columns=['id_saih', 'sensor'], errors='ignore')
                    .sort_index()
                    .asfreq(freq)
        for ID, group in data.groupby('id_saih')
    }
    timeseries = {ID: df.where(df >= 0) for ID, df in timeseries.items()}

    return timeseries