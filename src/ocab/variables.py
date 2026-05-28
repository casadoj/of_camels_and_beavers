# variables.py

DECIMALS = {
    'discharge_cms': 3,
    'discharge_mm': 6,
    'temp_degC': 6,
    'temp_max_degC': 6,
    'temp_max_degC': 6,
    'precip_mm': 6,
    'pet_mm': 6,
}

RENAME = {
    # temperature
    'ta_mean': 'temp_degC', 
    'maxtemp_mean': 'temp_max_degC',
    'mintemp_mean': 'temp_min_degC',
    # precipitation
    'pr_mean': 'precip_mm', 
    'precipitation_mean': 'precip_mm',
    # potential evapotranspiration
    'e0_mean': 'pet_mm',
    'pet_mean': 'pet_mm'
}