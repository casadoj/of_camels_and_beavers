# 1 Pretratamiento

En esta carpeta se incluyen los _notebooks_ utilizados en el pretratamiento de datos necesario para generar el conjunto de datos CAMELS-ES.

### Anuario de Aforos
* *1_Anuario_seleccion_estaciones.ipynb*: se cargan los datos del Anuario de Aforos y se hace la selección de las estaciones que se incluiran en CAMELS-ES. Como resultado se obtienen las capas GIS de puntos con las estaciones del Anuario, definiendo aquéllas seleccionadas o descartadas.

### EMO1
* *2_EMO1_series_areales.ipynb*: se calculan las series areales diarias de las cuencas de CAMELS-ES a partir de los datos de EMO1 (European Meteorological Observations): precipitación, temperatura media y evapotranspiración.

### EFAS5
* *3.1_EFAS5_reporting_points.ipynb*: se comparan las estaciones seleccionadas del Anuario de Aforos con los puntos de EFAS calibrados.
* *3.2_EFAS5_extraer_caudal.ipynb*: se extraen las series temporals de caudal simulado en EFAS5 para las estaciones de CAMELS-ES.
* *3.3_EFAS5_atributos.ipynb*: se calculan los atributos de las cuencas de CAMELS-ES a partir de los mapas estáticos de EFAS5, de los mapas de parámetros calibrados, y de la meteorología de EMO1.

### Caravan
* *4.1_Caravan_datos_auxiliares.ipynb*: se generan los datos auxiliares necesarios para crear CAMELS-ES, es decir, las series de caudal específico y la capa polígonos con las cuencas.
* *4.2_Caravan_explorar_dataset.ipynb*: se analizan qué datos se incluyen en CAMELS-ES.

### Artículo
* *5_plots_articulos.ipynb*: se crean algunos de los gráficos del documento final.