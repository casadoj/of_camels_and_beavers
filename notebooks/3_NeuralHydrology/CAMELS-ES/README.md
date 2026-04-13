# LSTM-CAMELS-ES

Tras varias pruebas con un número menor de cuencas y series más cortas, se entrenó un primer modelo **base**. A partir de este modelo se hizo un pequeño análisis de sensibilidad para estudiar qué hiperparámetros eran los más sensibles. Posteriormente se escogieron los parámetros más sensibles y se reentrenaron los modelos llamados **end**, que son pequeñas variaciones del modelo **base** en la que se modifica alguno de los parámetros sensibles.

| Modelo    | `batch_size` | `hidden_size` | `dropout` | `clip_gradient_norm` |
| --------- | ------------ | ------------- | --------- | -------------------- |
| base      | 256 | 64  | 0.4 | 1   |
| batch128  | 128 | 64  | 0.4 | 1   |
| batch512  | 512 | 64  | 0.4 | 1   |
| clip0.8   | 256 | 64  | 0.4 | 0.8 |
| clipNone  | 256 | 64  | 0.4 |     |
| drop03    | 256 | 64  | 0.3 | 1   |
| drop05    | 256 | 64  | 0.5 | 1   |
| hidden032 | 256 | 32  | 0.4 | 1   |
| **hidden128** | **256** | **128** | **0.4** | **1**   |
| end       | 256 | 128 | 0.5 | 0.8 |
| end2      | 512 | 128 | 0.4 | 1   |
| end3      | 256 | 128 | 0.4 | 0.8 |


De estos modelos el mejor rendimiento se obtuvo para el llamado **hidden128**.