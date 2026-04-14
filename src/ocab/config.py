import yaml
import pandas as pd
from pathlib import Path

class Config:
    def __init__(self, config_file="../config.yml"):
        # Load configuration from YAML file
        with open(config_file, "r", encoding='utf8') as ymlfile:
            self.cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        
        # DATASET CONFIGURATION

        cfg_dataset = self.cfg['dataset']
        
        # name and version
        self.name = cfg_dataset['name']
        self.version = cfg_dataset['version']

        # Start and end of the study period
        self.start = pd.to_datetime(cfg_dataset['period'].get('start', None))
        self.end = pd.to_datetime(cfg_dataset['period'].get('end', None))

        # Minimum and maximun catchment size
        if 'area' in cfg_dataset:
            self.area_min = cfg_dataset['area'].get('min', 0)  # km²
            self.area_max = cfg_dataset['area'].get('max', None)  # km²

        # Minimum and maximun reservoir size
        if 'volume' in cfg_dataset:
            self.volume_min = cfg_dataset['volume'].get('min', 0)  # hm³
            self.volume_max = cfg_dataset['volume'].get('max', None)  # hm³

        # Data availability in the study period
        self.availability = cfg_dataset['data'].get('availability', .8)
        self.min_years = cfg_dataset['data'].get('years', 10)

        # Coordinate system
        self.crs = cfg_dataset.get('crs', 4326)

        # PATH CONFIGURATION

        paths = self.cfg['paths']

        # Input and output paths
        self.path_records = Path(paths['records'])
        self.path_dataset = Path(paths['dataset']) / self.name / f'v{'_'.join(self.version.split('.'))}'
        self.path_attributes = self.path_dataset / 'attributes'
        self.path_timeseries = self.path_dataset / 'timeseries'
        self.path_gis = self.path_dataset / 'GIS'
        self.path_plots = self.path_dataset / 'plots'
        self.path_efas = Path(paths.get('EFAS', None))
        self.path_merit = Path(paths.get('MERIT', None))
        self.path_meteo = Path(paths.get('meteo', None))

        # Ensure directories exist
        for path in [self.path_gis, self.path_plots]:
            path.mkdir(parents=True, exist_ok=True)
