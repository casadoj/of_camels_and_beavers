
from typing import Union
import logging
import re

import pandas as pd
import geopandas as gpd


logger = logging.getLogger(__name__)


def _check_names(serie: pd.Series):
    serie[:] = [re.split(r'[/|(]', str(name).strip())[0].strip().title() for name in serie]
    return serie


def update_attributes(
        primary: Union[pd.DataFrame, gpd.GeoDataFrame],
        secondary: Union[pd.DataFrame, gpd.GeoDataFrame],
        sort: bool = True
) -> Union[pd.DataFrame, gpd.GeoDataFrame]:
    """
    Update the primary DataFrame with attributes from a secondary DataFrame.

    Fills missing values in the primary DataFrame using values from intersecting 
    columns in the secondary DataFrame and appends any columns that exist 
    exclusively in the secondary DataFrame.

    Parameters
    ----------
    primary : pd.DataFrame or gpd.GeoDataFrame
        The base DataFrame or GeoDataFrame to be updated.
    secondary : pd.DataFrame or gpd.GeoDataFrame
        The source DataFrame or GeoDataFrame providing the new data.
    sort : bool, default True
        If True, sorts columns alphabetically. If a 'geometry' column is present, 
        it is moved to the end of the DataFrame.

    Returns
    -------
    pd.DataFrame or gpd.GeoDataFrame
        The updated DataFrame or GeoDataFrame with merged attributes.

    Raises
    ------
    AssertionError
        If the index names of `primary` and `secondary` are not identical.

    Notes
    -----
    This function uses `combine_first` for intersecting columns, meaning existing 
    non-null values in the `primary` DataFrame are preserved.
    """

    primary = primary.copy()
    secondary = secondary.copy()

    assert primary.index.name == secondary.index.name, 'Ensure that the indices of both input DataFrames are aligned'

    # update missing values in intersecting columns
    for col in primary.columns.intersection(secondary.columns):
        primary[col] = primary[col].combine_first(secondary[col])
        
    # add new columns
    for col in secondary.columns.difference(primary.columns):
        primary[col] = secondary[col]

    # sort columns
    if sort:
        cols = sorted([col for col in primary.columns if col != 'geometry'])
        if 'geometry' in primary.columns:
            cols += ['geometry']
        primary = primary[cols]

    return primary


def reset_index(
        gdf: gpd.GeoDataFrame,
        mapping: pd.Series,
        dropna: bool = True,
) -> gpd.GeoDataFrame:
    """
    Reindex a GeoDataFrame based on a provided mapping Series.

    Inverts the provided mapping to translate current index values to a new 
    set of identifiers, updates the index, and optionally drops unmapped rows.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        The GeoDataFrame whose index needs to be reset.
    mapping : pd.Series
        A Series where the index represents the new identifiers and the 
        values represent the current index values of the `gdf`.
    dropna : bool, default True
        Whether to remove rows where the current index could not be mapped 
        to a new value.

    Returns
    -------
    gpd.GeoDataFrame
        The GeoDataFrame with the new index applied and sorted.

    Notes
    -----
    The new index is cast to 'Int64' to support nullable integers.
    """

    gdf = gdf.copy()

    # invert mapping
    inverse_mapping = pd.Series(data=mapping.index, index=mapping.values)
    inverse_mapping = inverse_mapping[mapping.index.notnull()]
    name = mapping.index.name

    # reset index
    gdf[name] = gdf.index.map(inverse_mapping).astype('Int64')
    if dropna:
        gdf = gdf.dropna(subset=[name])
    gdf = gdf.reset_index().set_index(name).sort_index()

    return gdf


def encode_reservoir_use(
        df: pd.DataFrame,
        col_use: str,
        sort: bool = True
):
    """
    Split, translate, and one-hot encode reservoir usage categories.

    Processes a column containing newline-separated usage strings, translates 
    them to English, extracts the primary use, and generates OHE columns.

    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame containing reservoir data.
    col_use : str
        The name of the column containing usage strings (e.g., 'Riego\nAbastecimiento').
    sort : bool, default True
        If True, sorts columns alphabetically, keeping 'geometry' at the end.

    Returns
    -------
    pd.DataFrame
        The transformed DataFrame with new OHE columns and 'main_use'.
    """

    df = df.copy()

    # translation and column name for uses
    # comment @casadoj: 'Industrial' and 'Minería' are not classes in GDW
    #                   'Recreation' ,'Pollution Control', 'Fisheries', 'Multipurpose',
    #                   and 'Navigation' classes in GDW are not necessary.
    translate_use = {
        'Abastecimiento': 'Water supply',
        'Defensa frente avenidas': 'Flood control',
        'Ganadero': 'Livestock',
        'Hidroeléctrico': 'Hydroelectricity',
        'Industrial': 'Industrial',
        'Minería': 'Mining',
        'Regulación': 'Other',
        'Riego': 'Irrigation',
    }
    col_names = {
        'Abastecimiento': 'use_supp',
        'Defensa frente avenidas': 'use_fcon',
        'Ganadero': 'use_live',
        'Hidroeléctrico': 'use_elec',
        'Industrial': 'use_ind',
        'Minería': 'use_mine',
        'Regulación': 'use_othr',
        'Riego': 'use_irri',
    }

    # split uses into lists
    uses_series = df[col_use].astype('string').str.split('\n')

    # extract main use
    df['main_use'] = uses_series.str[0].map(translate_use)

    # one-hot encoder of uses
    uses_ohe = pd.get_dummies(uses_series.explode()).groupby(level=0).max()
    uses_ohe = uses_ohe[uses_ohe.columns.intersection(col_names)]
    uses_ohe = uses_ohe.rename(columns=col_names)

    # concatenate and cleanup
    df = pd.concat((df, uses_ohe), axis=1).drop(columns=[col_use])

    if sort:
        cols = sorted([col for col in df.columns if col != 'geometry'])
        if 'geometry' in df.columns:
            cols += ['geometry']
        df = df[cols]

    return df