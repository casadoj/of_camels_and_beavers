import numpy as np
import pandas as pd
import logging
import matplotlib.pyplot as plt

# crear logger
FRND_logger = logging.getLogger('metricas_rendimiento')


def NSE(observado, simulado):
    """Calcula el coeficiente de eficiencia de Nash-Sutcliffe.
    
    Parámetros:
    -----------
    observado:   series. Serie observada
    simulado:    series. Serie simulada"""
    
    # Eliminar pasos sin dato
    data = pd.concat((observado, simulado), axis=1)
    data.columns = ['obs', 'sim']
    data.dropna(axis=0, how='any', inplace=True)
    # Para la función si no hay datos
    if data.shape[0] == 0:
        FRND_logger.error('No hay valores')
        return
    # Calcular NSE
    nse = 1 - sum((data.obs - data.sim)**2) / sum((data.obs - data.obs.mean())**2)
    
    return nse


def RMSE(serie1, serie2):
    """Calcula la raíz del error medio cuadrático.
    
    Parámetros:
    -----------
    serie1:    series. Primera del par de series a comparar
    serie2:    series. Segunda del par de series a comparar"""
    
    data = pd.concat((serie1, serie2), axis=1)
    data.columns = ['obs', 'sim']
    # Eliminar pasos sin dato
    data.dropna(axis=0, how='any', inplace=True)
    # Para la función si no hay datos
    if data.shape[0] == 0:
        FRND_logger.error('No hay valores')
        return 
    # Calcular RMSE
    rmse = np.sqrt(sum((data.obs - data.sim)**2) / data.shape[0])
    
    return rmse


def sesgo(observado, simulado):
    """Calcula el sesgo del hidrograma, es decir, el porcentaje de error en el volumen simulado.
    
    sesgo = (Vsim - Vobs) / Vobs * 100
    
    Parámetros:
    -----------
    observado:   series. Serie observada
    simulado:    series. Serie simulada"""
    
    # Eliminar pasos sin dato
    data = pd.concat((observado, simulado), axis=1)
    data.columns = ['obs', 'sim']
    data.dropna(axis=0, how='any', inplace=True)
    # Para la función si no hay datos
    if data.shape[0] == 0:
        FRND_logger.error('No hay valores')
        return 
    # Calcular el sesgo    
    return (data.sim.sum() - data.obs.sum()) / data.obs.sum() * 100

  
def KGE(observado, simulado, sa=1, sb=1, sr=1):
    """Calcula el coeficiente de eficiencia de Kling-Gupta.
    
    Parámetros:
    -----------
    observado:   series. Serie observada
    simulado:    series. Serie simulada
    sa, sb, sr: integer. Factores de escala de los tres términos del KGE: alpha, beta y coeficiente de correlación, respectivamente
    
    Salida:
    -------
    KGE:        float. Eficienica de Kling-Gupta"""
    
    # Eliminar pasos sin dato
    data = pd.concat((observado, simulado), axis=1)
    data.columns = ['obs', 'sim']
    data.dropna(axis=0, how='any', inplace=True)
    # Para la función si no hay datos
    if data.shape[0] == 0:
        return

    # calcular cada uno de los términos del KGE
    alpha = data.sim.std() / data.obs.std()
    beta = data.sim.mean() / data.obs.mean()
    r = np.corrcoef(data.obs, data.sim)[0, 1]
    
    # Cacular KGE
    ED = np.sqrt((sr * (r - 1))**2 + (sa * (alpha - 1))**2 + (sb * (beta - 1))**2)
    KGE = 1 - ED
    
    return KGE, alpha, beta, r



def KGEmod(observado, simulado, sa=1, sb=1, sr=1):
    """Calcula el coeficiente de eficiencia de Kling-Gupta.
    
    Parámetros:
    -----------
    observado:   series. Serie observada
    simulado:    series. Serie simulada
    sa, sb, sr: integer. Factores de escala de los tres términos del KGE: alpha, beta y coeficiente de correlación, respectivamente
    
    Salida:
    -------
    KGE:        float. Eficienica de Kling-Gupta"""
    
    # Eliminar pasos sin dato
    data = pd.concat((observado, simulado), axis=1)
    data.columns = ['obs', 'sim']
    data.dropna(axis=0, how='any', inplace=True)
    # Para la función si no hay datos
    if data.shape[0] == 0:
        return

    # calcular cada uno de los términos del KGE
    alpha = (data.sim.std() / data.sim.mean()) / (data.obs.std() / data.obs.mean())
    beta = data.sim.mean() / data.obs.mean()
    r = np.corrcoef(data.obs, data.sim)[0, 1]
    
    # Cacular KGE
    ED = np.sqrt((sr * (r - 1))**2 + (sa * (alpha - 1))**2 + (sb * (beta - 1))**2)
    KGE = 1 - ED
    
    return KGE, alpha, beta, r
    


def matriz_confusion(obs, sim):
    """Calcula la matriz de confunsión del acierto en la ocurrencia o ausencia de precipitación diaria.
    
    Parámetros:
    -----------
    obs:       series. Serie observada
    sim:       series. Serie simulada"""
    
    data = pd.concat((obs, sim), axis=1)
    data.columns = ['obs', 'sim']
    # convertir días de lluvia en 1
    data[data > 0] = 1
    # Eliminar pasos sin dato
    data.dropna(axis=0, how='any', inplace=True)
    # Para la función si no hay datos
    if data.shape[0] == 0:
        FRND_logger.error('Series no coincidentes')
    # días con lluvia en la observación
    data1 = data[data.obs ==1]
    # días secos en la observación
    data0 = data[data.obs == 0]
    # calcular acierto
    acierto00 = sum(data0.sim == 0) / data0.shape[0]
    acierto01 = sum(data0.sim == 1) / data0.shape[0]
    acierto10 = sum(data1.sim == 0) / data1.shape[0]
    acierto11 = sum(data1.sim == 1) / data1.shape[0]
    acierto = [[acierto00, acierto01],
               [acierto10, acierto11]]
    acierto = pd.DataFrame(acierto, index=['obs0', 'obs1'], columns=['sim0', 'sim1'])
    
    return acierto


def logBiasNSE(obs, sim):
    """Calcula el coeficiente de eficiencia penalizado con el sesgo.
    
        logBiasNSE = NSE - 5 * abs(ln(1 + bias))**2.5
    
    Parámetros:
    -----------
    obs:       series. Serie observada
    sim:       series. Serie simulada"""
    
    # calcular Nash-Sutcliffe y error en volumen
    nse = NSE(obs, sim)
    bias = sesgo(obs, sim) / 100
    # calcular la función objetivo    
    return nse - 5 * abs(np.log(1 + bias))**2.5



def ECDF(serie, plot=True, **kwargs):
    """Calcula (y dibuja) la función de distribución empírica (empirical cumulative distribution function, ECDF) de una serie

    Parámetros:
    -----------
    serie:     pd.Series. Serie de la que se quiere calcular la ECDF
    plot:      boolean. Si se quiere generar un gráfico de la ECDF

    Salida:
    -------
    ecdf:      pd.Series. Serie que contiene la ECDF. El íncide es la probabilidad de no excedencia y los valores los mismos de la serie de entrada, pero ordenados ascendentemente
    """

    # ordenar valores
    ecdf = pd.Series(data=serie.sort_values().values,
                     index=np.arange(1, serie.shape[0] + 1) / serie.count(),
                     name='ECDF')

    if plot:
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.plot(ecdf.index, ecdf, lw=kwargs.get('lw', 1), c=kwargs.get('c', 'steelblue'))
        ax.set(ylim=kwargs.get('xlim', (-1.02, 1.02)), ylabel=kwargs.get('ylabel', serie.name),
               xlim=(-.02, 1.02), xlabel='ECDF (-)',
               title=kwargs.get('title', ''));

    return ecdf
