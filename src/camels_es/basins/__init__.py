import logging
import yaml
from pathlib import Path
from typing import Dict, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
import rioxarray as rxr

# set logger
logger = logging.getLogger(__name__)

class Config:
    """
    Manages the application's configuration by reading a YAML file
    and setting default values.
    """
    
    def __init__(self, config_file: Path):
        """
        Reads the configuration from a YAML file and sets default values if not provided.

        Parameters:
        -----------
        config_file: string or pathlib.Path
            The path to the YAML configuration file.
        """
        
        # extract the working directory
        config_file = Path(config_file).resolve()
        self.base_path = config_file.parent

        # read configuration file
        with open(config_file, 'r', encoding='utf8') as ymlfile:
            config = yaml.load(ymlfile, Loader=yaml.FullLoader)
            
        # input file paths
        inputs = config['input']
        self.points = self._absolute_path(inputs.get('points', None))
        self.points_fine = self._absolute_path(inputs.get('points_fine', None))
        self.basins_fine = self._absolute_path(inputs.get('basins_fine', None))
        self.ldd_fine = self._absolute_path(inputs.get('ldd_fine', None))
        self.upstream_fine = self._absolute_path(inputs.get('upstream_fine', None))
        self.ldd_coarse = self._absolute_path(inputs.get('ldd_coarse', None))
        self.upstream_coarse = self._absolute_path(inputs.get('upstream_coarse', None))

        # tasks to be done
        if self.points is None:
            self.run_fine = False
            if (self.points_fine is None) or (self.basins_fine is None):
                raise ValueError("If 'points' is not provided, both 'points_fine' and 'basins_fine' need to be provided.")
            else:
                self.run_coarse = True
        else:
            self.run_fine = True
            if (self.ldd_coarse is None) or (self.upstream_coarse is None):
                self.run_coarse = False
            else:
                self.run_coarse = True

        # resolutions
        self.fine_resolution = None
        self.coarse_resolution = None
        
        # output folder
        self.output_folder = self._absolute_path(config.get('output_folder', 'output'))
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        # conditions
        conditions = config['conditions']
        self.min_area = conditions.get('min_area', 10)
        self.abs_error = conditions.get('abs_error', 50)
        self.pct_error = conditions.get('pct_error', 1)
        
    def update_config(
        self,
        inputs: dict,
        # fine_grid: Optional[xr.DataArray],
        # coarse_grid: Optional[xr.DataArray]
    ):
        """
        Extracts the resolution from the finer and coarser grids and updates the configuration object.

        Parameters:
        -----------
        inputs: dictionary
            Dictionary that contains all the input data defined in the YAML configuration file    
        """

        # resolution of the finer grid
        if inputs['ldd_fine'] is not None:
            cellsize = np.mean(np.diff(inputs['ldd_fine'].x)) # degrees
            cellsize_arcsec = int(np.round(cellsize * 3600, 0)) # arcsec
        else:
            cellsize_arcsec = list(set([col.split('_')[1] for col in inputs['points_fine'].columns  if ('_' in col) & (not col.endswith('error'))]))[0]
            cellsize_arcsec = int(cellsize_arcsec[:-3])
        logger.info(f'The resolution of the finer grid is {cellsize_arcsec} arcseconds')
        self.fine_resolution = f'{cellsize_arcsec}sec'

        # resolution of the input maps
        if inputs['ldd_coarse'] is not None:
            cellsize = np.round(np.mean(np.diff(inputs['ldd_coarse'].x)), 6) # degrees
            cellsize_arcmin = int(np.round(cellsize * 60, 0)) # arcmin
            logger.info(f'The resolution of the coarser grid is {cellsize_arcmin} arcminutes')
            self.coarse_resolution = f'{cellsize_arcmin}min'

    def _absolute_path(self, path_str: Optional[str]) -> Optional[Path]:
        """
        Helper function to join the "base_path" with relative paths from the YAML configuration file.
        """
        if path_str is None:
            return None
        path = Path(path_str)
        return path if path.is_absolute() else (self.base_path / path).resolve()
        
 
def read_input_files(cfg: Config) -> Dict:
    """
    Reads input files, updates the Config object, and returns a dictionary
    of the loaded data.
    
    Parameters:
    -----------
    cfg: Config
        Configuration object containing file paths and parameters.
        
    Returns:
    --------
    Dict
        A dictionary containing the loaded data:
        * 'points': geopandas.GeoDataFrame of input points
        * 'ldd_fine': xarray.DataArray of local drainage directions in the fine grid
        * 'upstream_fine': xarray.DataArray of upstream area (km2) in the fine grid
        * 'ldd_coarse': xarray.DataArray of local drainage directions in the coarse grid
        * 'upstream_coarse': xarray.DataArray of upstream area (m2) in the coarse grid
    """

    def open_raster(path):
        """Helper to open and squeeze a raster file."""
        return rxr.open_rasterio(path).squeeze(dim='band')
        
    # read upstream map with fine resolution
    if cfg.upstream_fine:
        upstream_fine = open_raster(cfg.upstream_fine)
        logger.info(f'Map of upstream area in the finer grid corretly read: {cfg.upstream_fine}')

    # read local drainage direction map
    if cfg.ldd_fine:
        ldd_fine = open_raster(cfg.ldd_fine)
        logger.info(f'Map of local drainage directions in the finer grid corretly read: {cfg.ldd_fine}')
    
    # read upstream area map of coarse grid
    if cfg.upstream_coarse:
        upstream_coarse = open_raster(cfg.upstream_coarse)
        logger.info(f'Map of upstream area in the coarser grid corretly read: {cfg.upstream_coarse}')

    # read local drainage direction map
    if cfg.ldd_coarse:
        ldd_coarse = open_raster(cfg.ldd_coarse)
        logger.info(f'Map of local drainage directions in the coarser grid correctly read: {cfg.ldd_coarse}')
    
    
    if cfg.points:
        # read points text file
        points = pd.read_csv(cfg.points, index_col='ID')
        points.columns = points.columns.str.lower()
        logger.info(f'Table of points correctly read: {cfg.points}')
        points = check_points(cfg, points, ldd_fine)

        # convert to geopandas and export as shapefile
        points = gpd.GeoDataFrame(
            points,
            geometry=gpd.points_from_xy(points['lon'], points['lat']),
            crs=ldd_fine.rio.crs
        )
        point_file = cfg.output_folder / f'{cfg.points.stem}.geojson'
        points.to_file(point_file, driver='GeoJSON')
        logger.info(f'The original points table has been exported to: {point_file}')

    else:
        # read points and basins in the finer resolution grid
        points_fine = gpd.read_file(cfg.points_fine).set_index('ID')
        basins_fine = gpd.read_file(cfg.basins_fine).set_index('ID')
    
    inputs = {
        'points': points if cfg.points else None,
        'ldd_fine': ldd_fine if cfg.ldd_fine else None,
        'upstream_fine': upstream_fine if cfg.upstream_fine else None,
        'points_fine': points_fine if cfg.points_fine else None,
        'basins_fine': basins_fine if cfg.basins_fine else None,
        'ldd_coarse': ldd_coarse if cfg.ldd_coarse else None,
        'upstream_coarse': upstream_coarse if cfg.upstream_coarse else None,
    }
    
    # update Config
    cfg.update_config(inputs)
    
    return inputs

    
def check_points(
    cfg: Config,
    points: pd.DataFrame,
    ldd: xr.DataArray
) -> pd.DataFrame:
    """
    Removes input points that have missing values, a small catchment area,
    or are outside the map extent.
    
    Parameters:
    -----------
    cfg: Config
        Configuration object.
    points: pandas.DataFrame
        Table of input points with fields 'lat', 'lon' and 'area' (km2)
    ldd: xarray.DataArray
        Map of local drainage directions
        
    Returns:
    --------
    pandas.DataFrame
        The input table with points with conflicts removed.
    """
    
    # remove points with missing values
    mask_nan = points.isnull().any(axis=1)
    if mask_nan.sum() > 0:
        points = points[~mask_nan]
        logger.warning(f'{mask_nan.sum()} points were removed because of missing values.')
        
    # remove points with small catchment area
    mask_area = points['area'] < cfg.min_area
    if mask_area.sum() > 0:
        points = points[~mask_area]
        logger.info(f'{mask_area.sum()} points were removed due to their small catchment area.')
        
    # remove points outside the input LDD map
    lon_min, lat_min, lon_max, lat_max = np.round(ldd.rio.bounds(), 6)
    mask_lon = (points.lon < lon_min) | (points.lon > lon_max)
    mask_lat = (points.lat < lat_min) | (points.lat > lat_max)
    mask_extent = mask_lon | mask_lat
    if mask_extent.sum() > 0:
        points = points[~mask_extent]
        logger.info(f'{mask_extent.sum()} points were removed because they are outside the input LDD map.')
        
    return points