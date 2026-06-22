# variables.py

DECIMALS = {
    # discharge
    'discharge_cms': 3,
    'discharge_mm': 6,
    'discharge_mm_sim': 6,
    # temperature
    'temp_degC': 6,
    'temp_dtr_degC': 6, 
    'temp_max_degC': 6,
    'temp_min_degC': 6,
    # precipitation
    'precip_frac': 6,
    'precip_mm': 6,
    'precip_max_mm': 6,
    'precip_std_mm': 6,
    # potential evapotranspiration
    'pet_mm': 6,
    # reservoir storage
    'storage_mcm': 3,
    'filling': 3,
    # reservoir level
    'level_masl': 3,
    # reservoir flows
    'inflow_cms': 3,
    'inflow_mm': 6,
    'outflow_cms': 3,
    'outflow_mm': 6,
}

RENAME = {
    # temperature
    'ta_mean': 'temp_degC', 
    'avgtemp_mean': 'temp_degC',
    'maxtemp_mean': 'temp_max_degC',
    'mintemp_mean': 'temp_min_degC',
    'rngtemp_mean': 'temp_dtr_degC',
    # precipitation
    'pr_mean': 'precip_mm', 
    'precipitation_frac': 'precip_frac',
    'precipitation_max': 'precip_max_mm',
    'precipitation_mean': 'precip_mm',
    'precipitation_std': 'precip_std_mm',
    # potential evapotranspiration
    'e0_mean': 'pet_mm',
    'pet_mean': 'pet_mm',
    # reservoir storage
    'storage': 'storage_mcm',
    # reservoir level
    'inflow': 'inflow_cms',
    'outflow': 'outflow_cms',
    # reservoir flows
    'level': 'level_masl',
}