# BEAVERS-ES

This folder contains the **notebooks** used to develop the dataset BEAVERS-ES v1.0.0 (_Basin and Reservoir Attributes, Volume, Evaporation and Release time Series - ESpaña_). This is a dataset that includes daily time series of reservoir operations (inflow, outflow and storage), as well as reservoir, dam and catchment characteristics.

* [_beavers_1_selection_](./beavers_1_selection.ipynb) loads the available data and does a first selection of reservoirs with enough data.
* [_beavers_2_meteo_CERRA-Land_](./beavers_2_meteo_CERRA-Land.ipynb) and [_beavers_2_mete_ROCIO-IBEB](./beavers_2_meteo_ROCIO-IBEB.ipynb) generate the daily meteorological time series from the CERRA-Land and ROCIO-IBEB datasets.
* [_beavers_3_attributes_EFAS_](./beavers_3_attributes_EFAS.ipynb) and [_beavers_3_attributes_meteo_](./beavers_3_attributes_meteo.ipynb) generate the catchment attributes from the European Flood Awareness (EFAS) static maps, and the climate indices from the meteorological time series generated in earlier notebooks.
* [_beavers_5_website_](./beavers_5_website.ipynb) loads all the time series (observed reservoir operations and meteorology) and produces the HTML plots shown in the [GitHub Pages](https://casadoj.github.io/of_camels_and_beavers/).

The dataset configuration is controlled by the [configuration file](./config_BEAVERS_v100.yml). There are another two YAML files:
* [_map_reservoirs_datasets.yml_](./map_reservoir_datasets.yml) maps the reservoir ID in the Ministry's database with the IDs in other datasets such as the national Inventory of Dams and Reservoirs (IDR) or the Global Dam Watch (GDW).
* [_map_reservoirs_stations.yml_](./map_reservoir_stations.yml) identifies the gauging stations directly upstream or downstream of a reservoir.