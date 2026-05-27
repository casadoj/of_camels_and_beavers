import numpy as np
from typing import Literal, Optional
import xarray as xr

def compute_pixel_area(
        ds: xr.Dataset, 
        proj: Optional[Literal['wgs_1984', 'rotated_pole']] = None
    ) -> xr.DataArray:
    """Computes the physical area (in square meters) of each pixel in a 
    rotated-pole grid using its 2D geographical lat/lon coordinates.
    """
    # 1. Define Earth's radius in meters
    if proj and proj in ds:
        try:
            attrs = ds[proj].attrs
            # calculate the Authalic Radius (Equal-Area Sphere Radius)
            a = attrs['semi_major_axis']
            f = 1 / attrs['inverse_flattening']
            e = np.sqrt(2 * f - f**2) # eccentricity
            R = a * np.sqrt(0.5 + (1 - e**2) / (4 * e) * np.log((1 + e) / (1 - e)))
        except:
            R = 6371007.181
    else:
            R = 6371007.181

    try:
        x_dim = ds.rio.x_dim
        y_dim = ds.rio.y_dim
    except AttributeError:
        raise AttributeError(
            "The dataset does not have rioxarray spatial dimensions set. "
            "Ensure rioxarray is imported and the CRS/coordinates are initialized."
        )
    
    # 2. Get resolution in radians
    d_lat = np.abs(np.gradient(ds[y_dim]))[0]
    d_lon = np.abs(np.gradient(ds[x_dim]))[0]
    
    d_lat_rad = np.radians(d_lat)
    d_lon_rad = np.radians(d_lon)

    # 3. Convert 2D geographic latitude array to radians
    lat_var = 'lat' if 'lat' in ds else('latitude' if 'latitude' in ds else y_dim)
    lat_rad = np.radians(ds[lat_var])

    # 4. Spherical grid cell area formula: Area = R² * cos(lat) * d_lat * d_lon
    area = (R**2) * np.cos(lat_rad) * d_lat_rad * d_lon_rad

    # 5. Clean up attributes
    area.name = 'area'
    area.attrs = {
         'units': 'm2',
         'long_name': 'Pixel Area',
         'description': 'Calculated using spherical authalic radius'
    }

    try:
        area = area.rio.write_crs(ds.rio.crs)
    except Exception:
         pass
    
    return area
