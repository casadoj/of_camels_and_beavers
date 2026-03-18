from typing import Optional, Union
from pathlib import Path
from typing import Literal, List, Optional, Tuple

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from .signatures import annual_runoff, baseflow_index, flashiness_index, slope_fdc


def plot_stations(
    geometry,
    area: Optional[pd.Series] = None,
    save: Union[str, Path] = None,
    **kwargs
):
    """Creates a map where stations are represented as dots. The size of the dots reflects the catchment area (if provided)
    
    Parameters:
    -----------
    geometry: gpd.GeoSeries
        Geometry of the points
    area: pandas.Series (optional)
        Reservoir catchment area (km2)
    save: str or pathlib.Path (optional)
        If provided, file where the plot will be saved
    """
    
    figsize = kwargs.get('figsize', (20, 5))
    title = kwargs.get('title', None)
    alpha = kwargs.get('alpha', .7)
    size = kwargs.get('size', 12)
    color = kwargs.get('color', 'steelblue')
    marker = kwargs.get('marker', 'o')
    
    # set up plot
    proj = ccrs.PlateCarree()
    fig, ax = plt.subplots(
        figsize=figsize, 
        subplot_kw={'projection': proj}
    )
    ax.add_feature(
        cfeature.NaturalEarthFeature('physical', 'land', '10m', edgecolor='face', facecolor='wheat'),#'lightgray'),
        alpha=.5,
        zorder=0
    )
    ax.add_feature(
        cfeature.NaturalEarthFeature('physical', 'rivers_lake_centerlines', '10m', edgecolor='lightslategrey', facecolor='none', linewidth=.5),
        alpha=0.7,
        zorder=1
    )
    if 'extent' in kwargs:
        ax.set_extent(kwargs['extent'], crs=proj)
    if title is not None:
        ax.text(.5, 1.125, title, horizontalalignment='center', verticalalignment='bottom', transform=ax.transAxes, fontsize=12)
    ax.axis('off')
    
    # plot reservoir poitns
    s = np.cbrt(area) if area is not None else size
    scatter = ax.scatter(
        geometry.x,
        geometry.y,
        s=s,
        c=color,
        marker=marker,
        alpha=alpha,
        zorder=2
    )  
    
    # legend
    # if area is not None:
    #     legend = ax.legend(
    #         *scatter.legend_elements(prop='sizes', num=4, alpha=alpha),
    #         title='catchment (km²)',
    #         # bbox_to_anchor=(1.2, 0.5),
    #         bbox_to_anchor=[1.025, .6, .06, .25],
    #         loc='center left',
    #         frameon=False
    #         )
    #     ax.add_artist(legend)    

    # save
    if save is not None:
        plt.savefig(save, dpi=300, bbox_inches='tight')


def plot_discharge(
    ts: pd.Series,
    area: float,
    regime: Optional[str] = None,
    save: bool = False,
    **kwargs
    ):
    """Creates an interactive figure with two plots: the hydrograph and the flow duration curve.
    Interactive buttons allow to transform the discharge data to logarithmic or square root scales
    to identify issues in the low flows.
    
    Parameters:
    -----------
    ts: pandas.Series
        Discharge time series
    area: float
        Catchment area (km²)
    regime: string (optional)
        Flow regime (if provided by the Ministry)
    save: boolean
        If True, return an object with the Plotly figure. If false, show the figure
    
    Keyword arguments:
    ------------------
    c: string
        Line colour
    title: string
        Figure title
    """

    # Extract keywords
    c = kwargs.get('c', 'steelblue')
    title = kwargs.get('title', None)

    # 1. Compute hydrological signatures
    ar = annual_runoff(ts, area)
    _, bfi = baseflow_index(ts)
    fi = flashiness_index(ts)
    fdc, slope = slope_fdc(ts)
    signature_text = (
        f"<b>Catchment Properties</b><br>"
        f"Area: {area:.0f} km²<br>"
        f"Regime: {regime}<br><br>"
        f"<b>Hydrological Signatures</b><br>"
        f"Baseflow Index: {bfi:.2f}<br>"
        f"Flashiness Index: {fi:.2f}<br>"
        f"Slope Flow Duration Curve: {slope:.2f}<br>"
        f"Annual Runoff: {ar:.0f} mm"
    )

    # 2. Create Subplots 
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, column_widths=[0.7, 0.25], horizontal_spacing=0.03,
                        subplot_titles=("Hydrograph", "Flow Duration Curve"))

    # 3. Add traces
    fig.add_trace(go.Scatter(x=ts.index, y=ts.values, line=dict(color=c, width=1), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=fdc.index * 100, y=fdc.values, line=dict(color=c, width=2), showlegend=False), row=1, col=2)    

    # 4. Update Layout
    fig.update_layout(
        title_text=f"<b>{title if title else ''}</b>",
        title_x=0.5,
        margin=dict(l=50, r=250, t=100, b=50),
        template="plotly_white",
        height=550,
        showlegend=False,
        annotations=[dict(
            text=signature_text,
            xref="paper", yref="paper",
            x=1.02, xanchor="left",
            y=1, yanchor="top",
            showarrow=False,
            align="left",
            font=dict(size=12),
            bgcolor="rgba(255, 255, 255, 0.9)",
        )],
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                active=0,
                x=0.0, xanchor="left",
                y=1.15,
                # aligh="left",
                buttons=[
                    dict(label="Linear Scale", method="update", 
                         args=[{"y": [ts.values, fdc.values]}, 
                               {"yaxis.type": "linear", "yaxis2.type": "linear", 
                                "yaxis.title.text": "Discharge (m³/s)"}]),
                    dict(label="Log Scale", method="update",
                         args=[{"y": [ts.values, fdc.values]}, 
                               {"yaxis.type": "log", "yaxis2.type": "log", 
                                "yaxis.title.text": "Discharge (log m³/s)"}]),
                    dict(label="Sqrt Scale", method="update",
                         args=[{"y": [ts.values**0.5, fdc.values**0.5]},
                               {"yaxis.type": "linear", "yaxis2.type": "linear", 
                                "yaxis.title.text": "Discharge (√m³/s)"}])
                ],
            )
        ]
    )

    # Update Axes Titles
    fig.update_yaxes(title_text="Discharge (m³/s)", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Exceedance Prob. (%)", row=1, col=2)

    if save:
        return fig
    else:
        fig.show()

def create_station_html(
    fig, 
    path: str,
    start: str,
    end: str
):
    """Wraps a Plotly figure into the full validation HTML template.
    
    Parameters:
    -----------
    fig:
        Result of `plot_discharge()`
    path: string
        Name of the HTML file where the figure wil be saved
    start: string
        Start date of the time series. Format YYYY-mm-dd
    end: string
        End date of the time series. Format YYYY-mm-dd
    """

    # Convert figure to HTML div string
    plotly_html = fig.to_html(
        full_html=False, 
        include_plotlyjs='cdn',
        config={'responsive': True}
    )

    full_page_html = f"""
        <html>
        <head>
            <meta charset="utf-8" />
            <style>
                body {{ 
                    margin: 0; padding: 0; height: 100vh; display: flex; 
                    flex-direction: column; font-family: sans-serif;
                }}
                .hydrograph {{ flex: 1; height: 50vh; width: 100%; overflow: hidden; }}
                .google-form {{ order: 2; height: 50vh; display: flex; }}
                iframe {{ width: 100%; height: 100%; border: none; }}
                .back-nav {{ position: fixed; top: 12px; left: 8px; z-index: 9999; }}
                .back-btn {{
                    text-decoration: none; color: steelblue; font-size: 14px; font-weight: bold; 
                    background-color: rgba(255, 255, 255, 0.9); padding: 8px 12px; 
                    border-radius: 5px; border: 1px solid #ccc;
                }}
            </style>
        </head>
        <body>
            <div class="back-nav">
                <a href="../../../index.html" class="back-btn">← Back to map</a>
            </div>
            <div class="hydrograph">{plotly_html}</div>
            <div class="google-form" id="form-container"></div>

            <script>
                (function() {{
                    const baseUrl = "https://docs.google.com/forms/d/e/1FAIpQLSdMDms_IAwkhPwOVqLvU0oVghG9Xti1LMhTsPoujm2w2uXF9A/viewform?embedded=true";
                    const emailEntryId = "2010975770";
                    const stationEntryId = "1301492004";
                    const startEntryId = "598747998";
                    const endEntryId = "2001326573";

                    const userEmail = localStorage.getItem('userEmail') || "";
                    const filename = window.location.pathname.split('/').pop();
                    const stationId = filename.replace('.html', '');
                    const start = "{start}";
                    const end = "{end}";

                    const finalUrl = baseUrl + 
                        "&entry." + stationEntryId + "=" + stationId + 
                        "&entry." + emailEntryId + "=" + encodeURIComponent(userEmail) + 
                        "&entry." + startEntryId + "=" + start + 
                        "&entry." + endEntryId + "=" + end;

                    document.getElementById('form-container').innerHTML = 
                        '<iframe src="' + finalUrl + '" frameborder="0">Loading form…</iframe>';
                }})();

                window.addEventListener('load', function() {{
                    setTimeout(function() {{ window.dispatchEvent(new Event('resize')); }}, 100); 
                }});
            </script>
        </body>
        </html>
        """
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(full_page_html)


def create_index(
        path: str, 
        title: str, 
        header: str, 
        index: List[Tuple],
        target: Literal['_self', '_blank'] = '_self',
        parent: Optional[str] = None
    ):
    """
    Crea un archivo 'index.html' en la ruta definida que permite el acceso a gráficos de las estaciones

    Parámetros:
    -----------
    path: str
        Ruta donde se guardará el archivo 'index.html'
    title: str
        Nombre que aparecerá en la pestaña del navegador
    header: str
        Título de la página
    index: list of tuples
        Lista de pares de valores: etiqueta que aparece en la página, enlace al archivo
    target: str
        Si se quiere que se abra una nueva pestaña ('_blank') o en la misma ('_self')
    parent: str
        Nombre de la página superior (en caso de existir)
    """
    

    # CSS for a modern, clean look
    css = """
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            max-width: 800px; 
            margin: 40px auto; 
            padding: 0 20px;
            background-color: #f8f9fa;
        }
        h1 { color: #2c3e50; border-bottom: 2px solid steelblue; padding-bottom: 10px; }
        .back-link { display: inline-block; margin-bottom: 20px; color: steelblue; text-decoration: none; font-weight: bold; }
        .back-link:hover { text-decoration: underline; }
        ul { list-style: none; padding: 0; }
        li { background: white; margin: 5px 0; padding: 10px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: 0.2s; }
        li:hover { transform: translateX(5px); box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        a.station-link { text-decoration: none; color: #2980b9; display: block; width: 100%; }
        a.station-link:hover { color: steelblue; }
    </style>
    """

    file = path / "index.html"
    with open(file, "w") as f:
        f.write("<!DOCTYPE html>\n<html>\n<head>\n")
        f.write(f"<meta charset='utf-8'>\n<title>{title}</title>\n{css}\n</head>\n")
        f.write("<body>\n")

        # link to parent folder
        if parent:
            f.write(f"<a href='../index.html' class='back-link'>← {parent}</a>\n")

        # header
        f.write(f"<h1>{header}</h1>\n")

        # list of links
        f.write("<ul>\n")
        for link, label in index:
            f.write(f"  <li><a class='station-link' href='{link}' target='{target}'>{label}</a></li>\n")
        f.write("</ul>\n</body>\n</html>")