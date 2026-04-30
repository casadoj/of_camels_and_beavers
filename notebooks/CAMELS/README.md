# CAMELS-ES

This folder contains the **notebooks** used to develop the dataset CAMELS-ES v2.0.0 (_Catchment Attributes and Meteorology for Large-Sample Studies - ESpaña_). This is a dataset that includes daily time series of observed river discharge and catchment meteorolgoy, as well as catchment characteristics.

* [_camels_1_selection_](./camels_1_selection.ipynb) loads the available data and does a first selection of stations with enough data.
* [_camels_2_meteo_CERRA-Land_](./camels_2_meteo_CERRA-Land.ipynb), [_camels_2_meteo_EMO1_](./camels_2_meteo_EMO1.ipynb) and [_camels_2_mete_ROCIO-IBEB](./camels_2_meteo_ROCIO-IBEB.ipynb) generate the daily meteorological time series from the CERRA-Land, EMO1 and ROCIO-IBEB datasets.
* [_camels_3_attributes_EFAS_](./camels_3_attributes_EFAS.ipynb) and [_camels_3_attributes_meteo_](./camels_3_attributes_meteo.ipynb) generate the catchment attributes from the European Flood Awareness (EFAS) static maps, and the climate indices from the meteorological time series generated in earlier notebooks.
* [_camels_4_website_](./camels_4_website.ipynb) loads all the time series (river discharge and meteorology) and produces the HTML plots shown in the [GitHub Pages](https://casadoj.github.io/of_camels_and_camels/).

The dataset configuration is controlled by the [configuration file](./config_CAMELS_v200.yml).