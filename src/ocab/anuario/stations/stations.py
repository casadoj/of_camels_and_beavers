import pandas as pd
import geopandas as gpd
from pathlib import Path
import logging

from .utils import _check_names


logger = logging.getLogger(__name__)


def get_gauges_basin(
        path: Path, 
        active: bool = False, 
        min_area: int = None, 
        max_area: int = None, 
        years: int = None, 
        epsg: int = 4326
    ) -> gpd.GeoDataFrame:
    """
    Extracts the attribute table of the ROEA stations from the 'estaf.csv' file of the 'Anuario de Aforos'.
    Stations can be filtered by area, by the number of years with available data, and by their current status.

    Parameters:
    -----------
    path:      str
        Path to the basin folder containing the file 'estaf.csv'.
    active:    boolean
        If True, only active stations are retained.
    min_area:  int or float
        Minimum basin area (km²) to include the station in the extraction.
    max_area:  int or float
        Maximum basin area (km²) to include the station in the extraction.
    years:     int
        Minimum number of years with available data.
    epsg:      int
        EPSG code of the coordinate system in which to project the points. The original 
        coordinates are in 25830 (ETRS89-UTM 30N), but the layer is generated in 
        4326 (WGS84) by default.

    Returns:
    -------
    geopandas.GeoDataFrame
        Point layer containing the stations.
    """

    if min_area is not None:
        assert min_area > 0, '"min_area" must be a positive integer.'
    if max_area is not None:
        if min_area is not None:
            assert max_area > min_area, '"max_area" must be larger than "min_area".'
        else:
            assert max_area > 0, '"max_area" must be a positive integer.'
    if years is not None:
        assert years > 0, '"years" must be a positive integer.'

    # load data
    stations = pd.read_csv(path / 'estaf.csv', sep=';', encoding='latin1')

    # rename and select columns
    rename_cols = {
        'indroea': 'id',
        'lugar': 'name',
        'comentario': 'comment',
        'serv': 'active',
        'suprest': 'catch_skm', # station
        'suprcnc': 'catch_skm_basin',
        'hoja_id': 'id_sheet',
        'alti': 'elev_masl',
        'altimax': 'elev_max_masl',
        'naa': 'years_daily',
        'naam': 'years_monthly',
        'naai': 'years_instant',
        'num_cuenca': 'id_basin',
        'muni_id': 'id_municipality',
        'xetrs89': 'x_etrs89',
        'yetrs89': 'y_etrs89',
        'longwgs84': 'lon_wgs84',
        'latwgs84': 'lat_wgs84',
        'cod_saih': 'id_saih'
    }
    stations = stations[rename_cols.keys()].rename(columns=rename_cols, errors='ignore')

    # set index
    stations.set_index('id', drop=True, inplace=True)
    stations.index = stations.index.astype(int)
    
    # handle fields
    stations.name = _check_names(stations.name)
    # stations.dropna(axis=1, how='all', inplace=True)
    stations[['lon_wgs84', 'lat_wgs84']] /= 1e4 

    # filters
    if active:
        stations = stations[stations.active != 0]
    if min_area is not None:
        stations = stations[~(stations.catch_skm < min_area)]
    if max_area is not None:
        stations = stations[~(stations.catch_skm > max_area)]
    if years is not None:
        stations = stations[~(stations.years_daily < years)]
    
    stations = gpd.GeoDataFrame(
        stations,
        geometry=gpd.points_from_xy(stations.x_etrs89, stations.y_etrs89),
        crs=25830
        )
    if epsg != 25830:
        stations = stations.to_crs(epsg)

    return stations


def get_gauges_miteco(
        file: Path, 
        active: bool = False, 
        min_area: int = None,
        epsg: int = 4326
) -> gpd.GeoDataFrame:
    """
    Extracts the attribute table of the gauging stations from "Ministerio de Transición ECOlógica".
    Stations can be filtered by area and by their current status.

    Parameters:
    -----------
    file:      str
        Path to the CSV file containing the gauging stations' attributes.
    active:    boolean
        If True, only active reservoirs are retained.
    min_area:  int or float
        Minimum basin area (km²) to include the station in the extraction.
    epsg:      int
        EPSG code of the coordinate system in which to project the points. The original 
        coordinates are in 25830 (ETRS89-UTM 30N), but the layer is generated in 
        4326 (WGS84) by default.

    Returns:
    -------
    geopandas.GeoDataFrame
        Point layer containing the gauging stations.
    """

    if min_area is not None:
        assert min_area > 0, '"min_area" must be a positive integer.'

    # load data
    stations = pd.read_csv(file, encoding='latin1')

    # rename columns
    stations.columns = stations.columns.str.lower()
    rename_cols = {
        # 'anch_rc': 'weir_width',
        'ano_fin_medidas': 'end',
        'ano_inicio_medidas': 'start',
        # 'caseta_rc': 'bridge',
        # 'cod_dma': ,
        'cod_hidro': 'id',
        # 'cod_masa_agua',
        'cod_saica': 'id_saica',
        'cod_saih': 'id_saih',
        # 'cod_situacion_estacion',
        'coord_utmx_h30_etrs89': 'x_etrs89',
        'coord_utmy_h30_etrs89': 'y_etrs89',
        'cota_z': 'elev_masl',
        'cuenca_recep': 'catch_skm',
        'cuenca_total': 'catch_skm_basin',
        'estado': 'active',
        # 'fotografia',
        'hoja_1_50000': 'sheet',
        # 'long_rc': 'weir_length',
        'nom_anuario': 'name',
        'num_cuenca': 'id_basin',
        'organismo_cuenca_visor': 'administration',
        # 'pasarela_rc': 'hut',
        # 'plano',
        'propietario': 'owner',
        'provincia': 'province',
        'regimen_rio': 'regime', 
        'rio': 'river',
        # 'seccion',
        # 'sensor_1': 'sensor', 
        'sistema_explo': 'system',
        # 'situacion_estacion',
        'termino_municipal': 'municipality',
        # 'tipo_caseta_rc': 'hut_type', 
        'tipo_esc_rc': 'scale_type', 
        'tipo_estacion': 'station_type', 
        'tipo_vert_rc': 'weir_type', 
        # 'transm_1', 
        'vertedero_rc': 'weir'
    }
    stations = stations[rename_cols.keys()].rename(columns=rename_cols)

    # handle data
    stations.name = _check_names(stations.name)
    stations.river = _check_names(stations.river)
    stations.active = stations.active.map({'ALTA': 1, 'BAJA': 0})
    for col in ['river', 'system']:
        stations[col] = stations[col].str.title()
    stations['regime'] = stations['regime'].str.lower()
    stations.regime = stations.regime.replace({
        'regulado': 'regulated',
        'muy modificado': 'regulated',
        'alterado': 'altered',
        '-': 'unkown',
        pd.NA: 'unkown',
    })
    stations.weir = stations.weir.replace({'Sí': True, 'y': True, pd.NA: False}).astype(bool)
    int_cols = ['start', 'end', 'id', 'id_basin']
    stations[int_cols] = stations[int_cols].astype('Int64')
    float_cols = ['catch_skm', 'catch_skm_basin', 'elev_masl']
    stations[float_cols] = stations[float_cols].astype(float)

    # set index
    stations.set_index('id', inplace=True)
    stations.sort_index(axis=0, inplace=True)
    stations.sort_index(axis=1, inplace=True)

    # filters
    if active:
        stations = stations[stations.active != 0]
    if min_area is not None:
        stations = stations[~(stations.catch_skm < min_area)]

    # convert to GeoDataFrame
    stations = gpd.GeoDataFrame(
        stations, 
        geometry=gpd.points_from_xy(stations.x_etrs89, stations.y_etrs89),
        crs=25830
    )
    if epsg != 25830:
        stations = stations.to_crs(epsg)

    return stations


def get_evaporimeters(
        file: Path, 
        active: bool = False, 
        years: int = None, 
        epsg: int = 4326
    ) -> gpd.GeoDataFrame:
    """Extrae la tabla de atributos de las estaciones evaporimétricas del Anuario de Aforos (archivo 'estev.csv'). 
    Se pueden filtrar las estaciones por número de años con datos y si están aún activas.

    Extracts the attribute table of the evaporimetric stations from the 'estev.csv' file of the 'Anuario de Aforos'.
    Stations can be filtered by the number of years with available data, and by their current status.

    Parámetros:
    -----------
    file:      str
        Path to the original file containing the stations.
    active:    boolean
        If True, only active stations are retained.
    years:     int
        Minimum number of years with available data.
    epsg:      int
        EPSG code of the coordinate system in which to project the points. The original 
        coordinates are in 25830 (ETRS89-UTM 30N), but the layer is generated in 
        4326 (WGS84) by default.

    Salida:
    -------
    geopandas.GeoDataFrame
        Point layer containing the stations.
    """

    assert years > 0, '"years" must be a positive integer.'

    # cargar datos
    stations = pd.read_csv(file, encoding='latin-1', sep=';')

    # rename and select columns
    rename_cols = {
        'alti': 'elev_masl',
        'comentario': 'comment', 
        'hoja_id': 'id_sheet',
        'latwgs84': 'lat_wgs84',
        'longwgs84': 'lon_wgs84',
        'lugar': 'name', 
        'muni_id': 'id_municipality',
        'nae': 'years',
        'num_cuenca': 'id_basin', 
        'ref_ceh': 'id',
        'ref_evap': 'id_evap',
        'serv': 'active', 
        'xetrs89': 'x_etrs89', 
        'yetrs89': 'y_etrs89',
    }
    stations = stations[rename_cols.keys()].rename(columns=rename_cols, errors='ignore')

    # set index
    stations.set_index('id_evap', drop=True, inplace=True)
    stations.index = stations.index.astype(int)
    
    # handle fields
    stations['id_ceh'] = stations['id_ceh'].astype('Int64')
    stations.name = stations.name.str.strip()
    # stations.dropna(axis=1, how='all', inplace=True)
    stations[['lon_wgs84', 'lat_wgs84']] /= 1e4

    # filters
    if active:
        stations = stations[stations.active != 0]
    if years is not None:
        stations = stations[~(stations.years < years)]

    # convertir en GeoDataFrame   
    stations = gpd.GeoDataFrame(
        stations,
        geometry=gpd.points_from_xy(stations.x_etrs89, stations.y_etrs89),
        crs=25830
        )
    if epsg != 25830:
        stations = stations.to_crs(epsg)

    return stations