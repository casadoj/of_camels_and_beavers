# Layers

## List of layers

* [_basin_authorities.geoson_](./basin_authorities.geojson): polygon layer of the administritative organization.
* [_reservoirs.geojson_](./reservoirs.geojson): polygon layer of the pre-selected reservoirs.
* [_reservoirs_basins_3sec.gejson_](./reservoirs_basins_3sec.geojson): polygon layer of the reservoir basins delineated using MERIT digital elevation map (3 arcsecond spatial resolution).
* [_rivers.geojson_](./rivers.geojson): polyline layer of main rivers.
* [_stations.geojson_](./stations.geojson): point layer of the pre-selected gauging stations (coordinates reported by the Ministry).
* [_stations_basins_3sec.gejson_](./stations_basins_3sec.geojson): polygon layer of the station basins delineated using MERIT digital elevation map (3 arcsecond spatial resolution).

## _stations.geojson_

| **Field** | **Units** | **Data type** |**Description** |
| --------- | --------- | ------------- |--------------- |
| active | - | int | 0: inactive, 1: active |
| administration | - | str | Administration responsible |
| basin | - | str | Name of the river basin |
| catch_skm | km² | float | Catchment area of the station |
| catch_skm_basin | km² | float | Catchment area of the whole river basin |
| comment | - | str | Comments |
| discharge | - | int | Are there discharge time series? 0: no, 1: yes |
| elev_masl | m | float | Altitude (meters above sea level) |
| elev_max_masl | m | flaot | Maximum altitude in the catchment (meters above sea level) |
| end | year | int | Year when the time series finish |
| id | - | int | ID of the gauging station. **Primary key**. | 
| id_basin | - | int | ID of the river basin |
| id_municipality | - | int | ID of the municipality |
| id_saih | - | int | Station ID in the regional system (_Sistema Automático de Información Hidrológica_) |
| id_sheet | - | int | ID of the National Topographic sheet where the staion is located |
| lat_wgs84 | degrees | float | Latitude in EPSG:4326 |
| lon_wgs84 | degrees | float | Longitude in EPSG:4326 |
| municipality | - | str | Name of the municipality |
| name | - | str | Station name |
| owner | - | str | Name of the station owner |
| province | - | str | Province |
| regime | - | str | Predefinition of the hydrological regime from the Ministry |
| river | - | str | River name |
| scale_type | - | str | Type of stage measurement |
| sheet | - | str | Name of the National Topographic sheet where the staion is located |
| start | year | int | Year when the time series start |
| station_type | - | str | Station type |
| system | - | str | Name of the hydrological system (subbasin) where the station is located |
| weir | - | bool | Whether the station has a weir or not |
| weir_type | - | str | Type of weir |
| x_etrs89 | m | float | X coordinate in EPSG:25830 |
| y_etrs89 | m | float | Y coordinate in EPSG:25830 |
| years_daily | year | int | Number of years with daily data |
| years_instant | year | int | Number of years with instantaneous data |
| years_monthly | year | int | Number of years with monthly data |

## _reservoirs.geojson_

| **Field** | **Units** | **Data type** |**Description** |
| --------- | --------- | ------------- |--------------- |
| active | - | int | 0: inactive, 1: active |
| administration | - | str | Administration responsible |
| area_skm | km² | float | Reservoir water surface area |
| basin | - | str | Name of the river basin |
| cap_mcm | hm³ | float | Reservoir storage capacity |
| catch_skm | km² | float | Catchment area of the station |
| category | - | str | Reservoir class in terms of size and risk |
| comment | - | str | Comments |
| dam_hgt_m | m | float | Dam height |
| dam_len_m | m | float | Length of the dam crest |
| dam_type | - | str | Type of dam |
| dis_avg_mcm | hm³ | float | Average annual inflow |
| dod_m | m | float | Degree of disruptivity: capacity by catchment area |
| elev_masl | m | float | Altitude (meters above sea level) |
| end | year | int | Year when the time series finish |
| estate | - | str | Estate where the reservoir is located |
| id | - | int | ID of the gauging station. **Primary key!** | 
| id_basin | - | int | ID of the river basin |
| id_gdw | - | int | Reservoir ID in the Global Dam Watch dataset |
| id_idr_dam | - | int | Dam ID in the national Inventory of Dams & Reservoirs |
| id_idr_res | - | int | Reservoir ID in the national Inventory of Dams & Reservoirs |
| id_municipality | - | int | ID of the municipality |
| id_saih | - | int | Station ID in the regional system (_Sistema Automático de Información Hidrológica_) |
| id_sheet | - | int | ID of the National Topographic sheet where the staion is located |
| inflow | - | int | Are there inflow time series? 0: no, 1: yes |
| lat_wgs84 | degrees | float | Latitude in EPSG:4326 |
| lon_wgs84 | degrees | float | Longitude in EPSG:4326 |
| main_use | - | str | Main use of the reservoir storage |
| municipality | - | str | Name of the municipality |
| mwl_elev_masl | m | float | Elevation at the Maximum Water Level |
| name | - | str | Station name |
| nwl_area_skm | km² | float | Water surface at the Normal Water Level |
| nwl_elev_masl | m | float | Elevation at the Normal Water Level | 
| operator | - | str | Who operates the reservoir |
| outflow | - | int | Are there outflow time series? 0: no, 1: yes |
| owner | - | str | Name of the station owner |
| owner_type | - | str | Type of owner |
| province | - | str | Province |
| reservoir_type | - | str | Type of reservoir
| river | - | str | River name |
| river_elev_masl | m | float | Elevation of the river at the dam location |
| scale_type | - | str | Type of stage measurement |
| sheet | - | str | Name of the National Topographic sheet where the staion is located |
| spillway_cms | m³/s | Capacity of the spillway |
| start | year | int | Year when the time series start |
| storage | - | int | Are there storage time series? 0: no, 1: yes |
| system | - | str | Name of the hydrological system (subbasin) where the station is located |
| timeline | - | str | Current status of the reservoir |
| use_elec | - | bool | Used for hydropower production|
| use_fcon | - | bool | Used for flood control |
| use_fish | - | bool | Used for fishing |
| use_ind | - | bool | Used for industry |
| use_irri | - | bool | Used for irrigation |
| use_live | - | bool | Used for livestock |
| use_mine | - | bool | Used for mining |
| use_navi | - | bool | Used for navigation |
| use_othr | - | bool | Other uses |
| use_pcon | - | bool | Used for pollution control |
| use_recr | - | bool | Used for recreation |
| use_supp | - | bool | Used for water supply |
| users | - | str | Users |
| x_etrs89 | m | float | X coordinate in EPSG:25830 |
| y_etrs89 | m | float | Y coordinate in EPSG:25830 |
| years_annual | year | int | Number of years with annual data |
| years_daily | year | int | Number of years with daily data |
| years_monthly | year | int | Number of years with monthly data |