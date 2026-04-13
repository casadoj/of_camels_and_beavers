# Simulación del caudal con LSTM

Este directorio contiene los modelos LSTM entrenados para simular el caudal, bien sea el observado bien el caudal simulado por EFAS5. 

## Modelos 

### CAMELS-ES
Modelo LSTM entrenado para simular el caudal observado en las cuencas de CAMELS-ES a partir de las series meteorológicas de ERA5 y los atributos de las cuencas de HydroATLAS.

### EFAS5
Modelo LSTM entrenado para emular el modelo hidrológico LISFLOOD-OS en su implementación en EFAS5. Para ello se utilizan las series meteorológicas de EMO1, los atributos extraídos de los mapas estáticos y los parámetros calibrados de LISFLOOD, y las series de caudal simuladas por EFAS5.

## Organización

Cada uno de los dos modelos se encuentran en su directorio correspondiente. En ambos casos, el directorio contiene lo siguiente:

* _Notebooks_ para el entrenamiento, comparación de modelos y análisis de resultados. El notebook *1_train_test.ipynb* está preparado para ser ejecutado en Google Colab, puesto que es necesario disponer de una GPU para acelerar el entrenamiento y simulación.
* Archivos *basins_?.txt* que definen las cuencas que conforman las muestras de entrenamiento, validación y test.
* Archivos *config_?.yml* con la configuración del LSTM para cada uno de los modelos entrenados. Los modelos entrenados se guardan dentro del subdirectorio `runs` con el nombre del modelo definido en el archivo de configuración y la fecha y hora cuando fueron entrenados.
* Archivos *periods_?.pkl* con los periodos de entrenamiento, validación y test para cada cuenca.

