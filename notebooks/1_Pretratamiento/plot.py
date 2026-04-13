import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.gridspec as gridspec
import cartopy.crs as ccrs
import cartopy.feature as cf
from matplotlib.cm import ScalarMappable
from typing import Dict, List, Tuple, Union
import geopandas as gpd
import pandas as pd
from pathlib import Path



def crear_cmap(cmap: str, bounds: List[float], name: str = '', specify_color: Tuple = None):
    """Given the name of a colour map and the boundaries, it creates a discrete colour ramp for future plots
    
    Inputs:
    ------
    cmap:          string. Matplotlib's name of a colourmap. E.g. 'coolwarm', 'Blues'...
    bounds:        list. Values that define the limits of the discrete colour ramp
    name:          string. Optional. Name given to the colour ramp
    specify_color: tuple (position, color). It defines a specific color for a specific position in the colour scale. Position must be an integer, and color must be either a colour name or a tuple of 4 floats (red, gren, blue, transparency)
    
    Outputs:
    --------
    cmap:   List of colours
    norm:   List of boundaries
    """
    
    cmap = plt.get_cmap(cmap)
    cmaplist = [cmap(i) for i in range(cmap.N)]
    if specify_color is not None:
        cmaplist[specify_color[0]] = specify_color[1]
    cmap = mpl.colors.LinearSegmentedColormap.from_list(name, cmaplist, cmap.N)
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    
    return cmap, norm



def rendimiento_LSTM(cuencas: gpd.GeoDataFrame, ecdf: Dict[str, pd.Series], metrica: str = 'KGE', referencia: str = None, demarcaciones: gpd.GeoDataFrame = None,
                     save: Union[str, Path] = None, **kwargs):
    """Crea una figura con el rendimiento del modelo LSTM según cuencas. La figura contiene dos gráficos, uno que muestra la función de distribución empírica de cada una de las muestras (entrenamiento, validación y evaluación), y otro que es un mapa que muestra la distribución geográfica del rendimiento.

    Parámetros:
    -----------
    cuencas:   gpd.GeoDataFrame
        Capa de los polígonos de las cuencas. Ha de incluir una columna con el nombre definido en "metrica" que define el rendimiento del modelo en esta cuenca
    ecdf:      Dict[str, pd.Series]
        Fundión de densidad empírica de las tres muestras (entrenamiento, validación y evaluación). El diccionario ha de tener tres entradas con cada una de las 3 muestras y dentro una serie con la ECDF
    metrica:   str
        Métrica de rendimiento. "cuencas" ha de contener una columna con este nombre
    referencia: str
        Clave de "ecdf" a utilizar como referencia
    demarcaciones: gpd.GeoDataFrame
        Opcional. Capa de polígonos con las demarcaciones hidrográficas (cuencas hidrográficas principales)
    save:      Union[str, Path]
        Opcional. Nombre y directorio donde se quiere guardar la figura

    kwargs:
    -------
    figsize:   List(2,)
        Tamaño de la figura
    extent:    List(4,)
        Extensión del mapa [xmin, xmax, ymin, ymax]
    proj:      str
        projección
    cmap:      str
        mapa de color para definir el rendimiento en el mapa
    """

    # extraer kwargs
    figsize = kwargs.get('figsize', (10, 3.75))
    extent = kwargs.get('extent', [-9.5, 3.5, 36, 44.5])
    proj = kwargs.get('proj', ccrs.PlateCarree())
    cmap = kwargs.get('cmap', 'RdBu')
    
    # mapa de color
    bounds = [-10, -1, -.75, -.5, -.25, 0, .25, .5, .75, 1]
    cmap, norm = crear_cmap(cmap, bounds, name=metrica)
    xticklabels = [str(i) for i in bounds]
    xticklabels[0] = ''

    # configuración de la figura
    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(1, 2)
    
    # función de densidad empírica
    ax1 = plt.subplot(gs[0])
    for (key, series), ls in zip(ecdf.items(), [':', '--', '-'] * 2):
        c = 'steelblue'
        if referencia is not None:
            if key == referencia:
                c, ls = 'maroon', '-'
        ax1.plot(series, label=key, lw=1.2, c=c, ls=ls)
    ax1.set(xlim=(-.01, 1.01),
            xlabel='ECDF (-)',
            ylim=(-1.02, 1.02),
            ylabel=f'{metrica} (-)')
    ax1.legend(frameon=False, loc=4);
    
    # mapa con el rendimiento de las cuencas
    ax2 = plt.subplot(gs[1], projection=proj)
    ax2.add_feature(cf.NaturalEarthFeature('physical', 'land', '10m', edgecolor=None, facecolor='lightgray'),
                   zorder=0)
    ax2.set_extent(extent, crs=proj)
    if demarcaciones is not None:
        demarcaciones.plot(ax=ax2, facecolor='none', edgecolor='w', linewidth=0.6, zorder=2)
    cuencas.plot(ax=ax2, column=metrica, cmap=cmap, norm=norm, alpha=1, zorder=1)
    ax2.axis('off')
    # colorbar
    cax = fig.add_axes([0.555, 0.05, 0.333, 0.025])
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, location='bottom', shrink=.5, cax=cax)
    cbar.set_label(f'{metrica} (-)', rotation=0)
    cbar.ax.tick_params(size=0)
    cax.set_xticklabels(xticklabels);

    if save is not None:
        plt.savefig(save, dpi=300, bbox_inches='tight');