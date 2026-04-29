import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
import logging
from typing import Optional, List, Dict

from .utils import encode_reservoir_use, _check_names

logger = logging.getLogger(__name__)


def get_dams_anuario(
        path: Path, 
        active: bool = False, 
        epsg: int = 4326
        ) -> gpd.GeoDataFrame:
    """
    Extracts the attribute table of the CEH reservoirs from the 'embalse.csv' file of the 'Anuario de Aforos' for
    a specific basin authority.
    Reservoirs can be filtered by their current status.

    Parameters:
    -----------
    path:      str
        Path to the basin folder containing the file 'embalse.csv'.
    active:    boolean
        If True, only active reservoirs are retained.
    epsg:      int
        EPSG code of the coordinate system in which to project the points. The original 
        coordinates are in 25830 (ETRS89-UTM 30N), but the layer is generated in 
        4326 (WGS84) by default.

    Returns:
    -------
    geopandas.GeoDataFrame
        Point layer containing the reservoirs.
    """

    # load data
    stations = pd.read_csv(path / 'embalse.csv', sep=';', encoding='latin1')
    
    # rename and select columns
    rename_cols = {
        'cod_saih': 'id_saih',
        'comentario': 'comment', 
        'hoja_id': 'id_sheet',
        'latwgs84': 'lat_wgs84',
        'longwgs84': 'lon_wgs84', 
        'mna': 'mwl_elev_masl', 
        'mnne': 'elev_masl', 
        'muni_id': 'id_municipality',
        'nae': 'years_annual',
        'naem': 'years_monthly', 
        'nom_embalse': 'name',
        'num_cuenca': 'id_basin', 
        'ref_ceh': 'id',
        'serv': 'active', 
        'xetrs89': 'x_etrs89', 
        'yetrs89': 'y_etrs89',
    }
    stations = stations[rename_cols.keys()].rename(columns=rename_cols, errors='ignore')

    # set index
    stations.set_index('id', drop=True, inplace=True)
    stations.index = stations.index.astype(int)
    
    # handle fields
    cols = ['elev_masl', 'mwl_elev_masl']
    stations[cols] = stations[cols].replace(0, np.nan)
    stations.name = _check_names(stations.name)
    # data.dropna(axis=1, how='all', inplace=True)
    stations[['lon_wgs84', 'lat_wgs84']] /= 1e4

    # filters
    if active:
        stations = stations[stations.active != 0]

    stations = gpd.GeoDataFrame(
        stations, 
        geometry=gpd.points_from_xy(stations.x_etrs89, stations.y_etrs89),
        crs=25830
    )
    if epsg != 25830:
        stations = stations.to_crs(epsg)

    return stations


def get_dams_miteco(
        file: Path, 
        active: bool = False, 
        min_area: int = None,
        min_volume: int = None,
        epsg: int = 4326
    ) -> gpd.GeoDataFrame:
    """
    Extracts the attribute table of the CEH reservoirs from "Ministerio de Transición ECOlógica".
    Reservoirs can be filtered by area, storage capacity, and by their current status.

    Parameters:
    -----------
    file:      str
        Path to the original file containing the reserv.
    active:    boolean
        If True, only active reservoirs are retained.
    min_area:  int or float
        Minimum basin area (km²) to include the station in the extraction.
    min_volume:  int or float
        Minimum storage capacity (hm³) to include the station in the extraction.
    epsg:      int
        EPSG code of the coordinate system in which to project the points. The original 
        coordinates are in 25830 (ETRS89-UTM 30N), but the layer is generated in 
        4326 (WGS84) by default.

    Returns:
    -------
    geopandas.GeoDataFrame
        Point layer containing the reservoirs.
    """

    if min_area is not None:
        assert min_area > 0, '"min_area" must be a positive integer.'
    if min_volume is not None:
        assert min_volume > 0, '"min_volume" must be a positive integer.'

    # load data
    stations = pd.read_csv(file, encoding='latin1')

    # rename columns
    stations.columns = stations.columns.str.lower()
    rename_cols = {
        'ano_fin_medidas': 'end',
        'ano_inicio_medidas': 'start',
        # 'cod_dma': ,
        'cod_hidro': 'id',
        # 'cod_masa_agua',
        # 'cod_saica',
        'cod_saih': 'id_saih',
        # 'cod_situacion_estacion',
        'coord_utmx_h30_etrs89': 'x_etrs89',
        'coord_utmy_h30_etrs89': 'y_etrs89',
        'cuenca_recep': 'catch_skm',
        'estado': 'active',
        # 'fotografia',
        'hoja_1_50000': 'sheet',
        'nmn_e': 'elev_masl',
        'nom_anuario': 'name',
        'organismo_cuenca_visor': 'administration',
        # 'plano',
        'propietario': 'owner',
        'provincia': 'province',
        'rio': 'river',
        # 'seccion',
        'sistema_explo': 'system',
        # 'situacion_estacion',
        'termino_municipal': 'municipality',
        'volumen_e': 'cap_mcm',
    }
    stations = stations[rename_cols.keys()].rename(columns=rename_cols)

    # handle data
    cols = ['cap_mcm', 'catch_skm', 'elev_masl']
    stations[cols] = stations[cols].replace(0, np.nan)
    stations.name = _check_names(stations.name)
    stations.river = _check_names(stations.river)
    stations.active = stations.active.map({'ALTA': 1, 'BAJA': 0})
    int_cols = ['start', 'end', 'id']
    stations[int_cols] = stations[int_cols].astype('Int64')
    float_cols = ['catch_skm', 'elev_masl', 'cap_mcm']
    stations[float_cols] = stations[float_cols].astype(float)

    # set index
    stations.set_index('id', inplace=True)
    stations.sort_index(axis=0, inplace=True)

    # filters
    if active:
        stations = stations[stations.active != 0]
    if min_area is not None:
        stations = stations[~(stations.catch_skm < min_area)]
    if min_volume is not None:
        stations = stations[~(stations.cap_mcm < min_volume)]

    # convert to GeoDataFrame
    stations = gpd.GeoDataFrame(
        stations, 
        geometry=gpd.points_from_xy(stations.x_etrs89, stations.y_etrs89),
        crs=25830
    )
    if epsg != 25830:
        stations = stations.to_crs(epsg)

    return stations


rename_IDR = {
    'ap_m_anual': 'dis_avg_mcm',
    'demarc': 'basin',
    # 'informe': 'link',
    'nmn_capac': 'cap_mcm',
    'nmn_sup': 'area_skm',
    'nombre': 'name',
    'provincia': 'province',
    'sup_cuenca': 'catch_skm',
    'titular': 'owner',
    'uso': 'use',
}

def get_reservoirs_IDR(
        file: Path,
        ids: Optional[List[int]] = None,
        min_area: int = None,
        min_volume: int = None
) -> gpd.GeoDataFrame:
    """
    Load and process reservoir data from the Inventory of Dams and Reservoirs (IDR).

    Reads a geospatial file, renames Spanish IDR fields to standardized English 
    attributes, processes reservoir usage categories, and filters by ID if provided.

    Parameters
    ----------
    file : Path
        Path to the source geospatial file (e.g., Shapefile, GeoJSON, or GPKG).
    ids : list of int, optional
        A list of specific reservoir IDs (`id_idr_res`) to retain. If None, 
        all records are returned.
    min_area:  int or float
        Minimum basin area (km²) to include the station in the extraction.
    min_volume:  int or float
        Minimum storage capacity (hm³) to include the station in the extraction.

    Returns
    -------
    gpd.GeoDataFrame
        Processed reservoir data indexed by 'id_idr_res' with sorted columns.
    """

    if min_area is not None:
        assert min_area > 0, '"min_area" must be a positive integer.'
    if min_volume is not None:
        assert min_volume > 0, '"min_volume" must be a positive integer.'

    # load data
    gdf = gpd.read_file(file)
    geometry = gdf.geometry
    crs = gdf.crs

    # handle columns
    gdf.columns = gdf.columns.str.lower()
    rename_cols = {
        'admon_comp': 'administration',
        'codigo': 'id_idr_res',
        'dtor_explo': 'operator',
        # 'id_embalse': 'id_idr_res',
        'nae_cota': 'mwl_elev_masl',
        'nmn_cota': 'elev_masl',
        'tipo_embal': 'reservoir_type',
        'tipo_titul': 'owner_type',
    }
    rename_cols.update(rename_IDR)
    df = gdf[rename_cols.keys()].rename(columns=rename_cols, errors='ignore')
    df.sort_index(axis=1, inplace=True)
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)
    
    # handle data
    cols = ['cap_mcm', 'catch_skm', 'area_skm', 'elev_masl', 'mwl_elev_masl']
    gdf[cols] = gdf[cols].replace(0, np.nan)
    gdf.name = _check_names(gdf.name)
    gdf = encode_reservoir_use(gdf, col_use='use')
    translate_reservoir_types = {
        'Embalse de presa': 'Dam reservoir',
        'Embalse de balsa': 'Off-stream reservoir'
    }
    gdf.reservoir_type = gdf.reservoir_type.map(translate_reservoir_types)

    # set index
    gdf.set_index('id_idr_res', inplace=True)
    if ids is not None:
        ids = gdf.index.intersection(ids)
        gdf = gdf.loc[ids]

    # filters
    if min_area is not None:
        gdf = gdf[~(gdf.catch_skm < min_area)]
    if min_volume is not None:
        gdf = gdf[~(gdf.cap_mcm < min_volume)]

    return gdf


def get_dams_IDR(
        file: Path,
        ids: Optional[List[int]] = None,
        min_area: int = None,
        min_volume: int = None 
) -> gpd.GeoDataFrame:
    """
    Load and process dam data from the Inventory of Dams and Reservoirs (IDR).

    Reads geospatial dam data, translates technical infrastructure fields 
    from Spanish to English, encodes usage types, and cleans geometry.

    Parameters
    ----------
    file : Path
        Path to the source geospatial file.
    ids : list of int, optional
        A list of specific dam IDs (`id_idr_dam`) to retain. If None, 
        all records are returned.
    min_area:  int or float
        Minimum basin area (km²) to include the station in the extraction.
    min_volume:  int or float
        Minimum storage capacity (hm³) to include the station in the extraction.

    Returns
    -------
    gpd.GeoDataFrame
        Processed dam data indexed by 'id_idr_dam' with sorted columns.
    """

    # load data
    gdf = gpd.read_file(file)
    geometry = gdf.geometry
    crs = gdf.crs

    # handle columns
    gdf.columns = gdf.columns.str.lower()
    rename_cols = {
        'alt_cimien': 'river_elev_masl',
        'cap_al_nae': 'spillway_cms', 
        'cap_max_df': 'outlet_cms',
        'categoria': 'category', 
        'cauce': 'river', 
        'ccaa': 'estate',
        # 'codigo': 'code', 
        'cota_coron': 'dam_elev_masl',
        'fase': 'timeline',
        'id_infraes': 'id_idr_dam', 
        'long_coron': 'dam_len_m',
        'tipo': 'dam_type', 
        'usuarios': 'users'
    }
    rename_cols.update(rename_IDR)
    df = gdf[rename_cols.keys()].rename(columns=rename_cols, errors='ignore')
    df.sort_index(axis=1, inplace=True)
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)

    # handle data
    cols = ['cap_mcm', 'catch_skm', 'dam_elev_masl', 'dam_len_m', 'area_skm', 'outlet_cms', 'river_elev_masl', 'spillway_cms']
    gdf[cols] = gdf[cols].replace(0, np.nan)
    gdf.name = _check_names(gdf.name)
    gdf = encode_reservoir_use(gdf, col_use='use')
    translate_dam_types = {
        'Presa de fábrica de arco-gravedad': 'Arch-gravity dam',
        'Presa de fábrica de bóveda': 'Arch dam',
        'Presa de fábrica de gravedad (hormigón compactado)': 'Gravity dam: Roller-Compacted Concrete',
        'Presa de fábrica de gravedad (hormigón vibrado)': 'Gravity dam: vibrated concrete',
        'Presa de fábrica de mampostería': 'Masonry dam',
        'Presa de fábrica de contrafuertes': 'Buttress dam',
        'Presa de materiales sueltos homogénea': 'Embankment dam: homogeneous',
        'Presa de materiales sueltos de pantalla asfáltica': 'Embankment dam: ssphalt-face',
        'Presa de materiales sueltos de pantalla de hormigón': 'Embankment dam: concrete-face',
        'Presa de materiales sueltos de pantalla de mampostería': 'Embankment dam: Masonry-face',
        'Presa de materiales sueltos zonificada o de núcleo': 'Embankment dam: zonified',
        'Presa mixta': 'Mixed/Composite dam',
    }
    gdf.dam_type = gdf.dam_type.map(translate_dam_types)
    translate_timeline = {
        'Explotación': 'In operation',
        'Puesta en carga': 'Initial impoundment',
        'Inundada': 'Inundated',
        'Proyecto abandonado': 'Abandoned project',
        'Proyecto': 'Under study'
    }
    gdf.timeline = gdf.timeline.map(translate_timeline)

    # set index
    gdf.set_index('id_idr_dam', inplace=True)
    if ids is not None:
        ids = gdf.index.intersection(ids)
        gdf = gdf.loc[ids]

    # filters
    if min_area is not None:
        gdf = gdf[~(gdf.catch_skm < min_area)]
    if min_volume is not None:
        gdf = gdf[~(gdf.cap_mcm < min_volume)]

    return gdf