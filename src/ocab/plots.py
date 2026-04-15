from typing import Optional, Union
from pathlib import Path
from typing import Literal, List, Optional, Tuple

import numpy as np
import pandas as pd
# import geopandas as gpd
# from shapely.geometry import box

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


# def plot_caudal(
#         serie: pd.Series, 
#         inicios: List[pd.Timestamp] = None, 
#         finales: List[pd.Timestamp] = None, 
#         save: str = None, 
#         **kwargs
#         ):
#     """Crea un gráfico de línea con el hidrograma de una estación de aforo.

#     Parámetros:
#     -----------
#     serie:     pd.Series
#         Serie de caudal
#     inicios:   List (3,)
#         Lista de fechas de inicio del periodo de entrenamiento, validación y evaluación
#     finales:   List (3,)
#         Lista de fechas de fin del periodo de entrenamiento, validación y evaluación
#     save:      str
#         Ruta donde guardar el gráfico. Por defecto es None y el gráfico no se guarda

#     kwargs:
#     -------
#     figsize:   tuple (2,)
#         Tamaño del gráfico
#     lw:        tuple (2,)
#         Grosor de línea
#     """

#     lw = kwargs.get('lw', .8)

#     fig, ax = plt.subplots(figsize=kwargs.get('figsize', (16, 4)))
#     if (inicios is None) or (finales is None):
#         ax.plot(serie, lw=lw)
#         ax.set_xlim(serie.first_valid_index(), serie.last_valid_index())
#     else:
#         assert len(inicios) == len(
#             finales), 'La longitud de las listas "inicios" y "finales" ha de ser la misma.'
#         for ini, fin in zip(inicios, finales):
#             if np.isnan(ini) or np.isnan(fin):
#                 continue
#             ax.plot(serie[ini:fin], lw=lw)
#         ax.set_xlim(np.nanmin(inicios), np.nanmax(finales))

#     ax.set(ylim=(0, None),
#            ylabel=kwargs.get('ylabel', 'Q (m3/s)'),
#            title=kwargs.get('title', None))

#     if save is not None:
#         plt.savefig(save, dpi=300, bbox_inches='tight')
#         plt.close(fig)


def plot_station_timeseries(
    ts: pd.DataFrame,
    area: float,
    regime: Optional[str] = None,
    save: bool = False,
    **kwargs
    ):
    """
    Creates an interactive figure with two plots: the hydrograph and the flow duration curve.
    Interactive buttons allow to transform the specific discharge and precipitation data to 
    logarithmic or square root scales to identify issues in the low flows.
    
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
    c_dis: string
        Color used to plot discharge
    c_precip: string
        Color used to plot precipitation
    title: string
        Figure title
    """

    # Extract keywords
    c_dis = kwargs.get('c_dis', 'indianred')
    c_precip = kwargs.get('c_precip', 'steelblue')
    title = kwargs.get('title', None)

    # Extract time series
    dis_cms = ts['discharge_cms']
    dis_mm = ts['discharge_mm']
    precip = ts['precip_mm']

    # 1. Compute hydrological signatures
    ar = annual_runoff(dis_cms, area)
    _, bfi = baseflow_index(dis_cms)
    fi = flashiness_index(dis_cms)
    fdc_dis, slope = slope_fdc(dis_mm)
    fdc_precip, _ = slope_fdc(precip)

    # Calculate Climatology values
    avg_precip = precip.mean()
    avg_temp = ts['temp_degC'].mean()
    avg_pet = ts['pet_mm'].mean()

    signature_text = (
        "<b>Catchment Properties</b><br>"
        f"Area: {area:.0f} km²<br>"
        f"Regime: {regime}<br>"
        "<br><b>Climatology</b><br>"
        f"Discharge: {ar:.0f} mm/year<br>"
        f"Precipitation: {avg_precip * 365:.0f} mm/year<br>"
        f"PET: {avg_pet * 365:.0f} mm/year<br>"
        f"Temperature: {avg_temp:.1f} °C<br>"
        "<br><b>Hydrological Signatures</b>"
        f"<br>Baseflow Index: {bfi:.2f}<br>"
        f"Flashiness Index: {fi:.2f}<br>"
        f"Slope FDC: {slope:.2f}<br>"
    )

    # 2. Create Subplots (Simple single Y-axis)
    fig = make_subplots(
        rows=1, cols=2, 
        shared_yaxes=True,
        column_widths=[0.7, 0.25], 
        horizontal_spacing=0.03,
        subplot_titles=("Hydrograph", "Flow Duration Curve")
    )

    # 3. Add traces
    # Trace 0: Precipitation (Background)
    fig.add_trace(
        go.Bar(x=ts.index, y=precip, name="Precipitation", marker_color=c_precip, opacity=0.6, showlegend=True),
        row=1, col=1
    )

    # Trace 1: Discharge (Foreground)
    fig.add_trace(
        go.Scatter(x=ts.index, y=dis_mm, name="Discharge", line=dict(color=c_dis, width=1), showlegend=True),
        row=1, col=1
    )

    # Trace 2: Flow Duration Curve of Precipitation (Background)
    fig.add_trace(
        go.Scatter(x=fdc_precip.index * 100, y=fdc_precip, name="Precipitation", line=dict(color=c_precip, width=2), opacity=0.6, showlegend=False),
        row=1, col=2
    )

    # Trace 3: Flow Duration Curve of Specific Discharge
    fig.add_trace(
        go.Scatter(x=fdc_dis.index * 100, y=fdc_dis.values, name="Discharge", line=dict(color=c_dis, width=2), showlegend=False),
        row=1, col=2
    )    

    # 4. Update Layout & Scale Buttons
    fig.update_layout(
        title_text=f"<b>{title if title else ''}</b>",
        title_x=0.5,
        margin=dict(l=50, r=275, t=100, b=50),
        template="plotly_white",
        height=550,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.35
        ),
        updatemenus=[
            dict(
                type="buttons", direction="right", active=0, x=0.0, xanchor="left", y=1.15,
                buttons=[
                    dict(label="Linear Scale", method="update", 
                         args=[
                             {"y": [precip, dis_mm, fdc_precip.values, fdc_dis.values]}, 
                             {"yaxis.type": "linear", "yaxis.title.text": "Water Depth (mm)"}
                         ]),
                    dict(label="Log Scale", method="update",
                         args=[
                             {"y": [precip, dis_mm, fdc_precip.values, fdc_dis.values]}, 
                             {"yaxis.type": "log", "yaxis.title.text": "Water Depth (log mm)"}
                         ]),
                    dict(label="Sqrt Scale", method="update",
                         args=[
                             {"y": [precip**0.5, dis_mm**0.5, fdc_precip.values**0.5, fdc_dis.values**0.5]},
                             {"yaxis.type": "linear", "yaxis.title.text": "Water Depth (√mm)"}
                         ])
                ],
            )
        ],
        annotations=[dict(
            text=signature_text, xref="paper", yref="paper",
            x=1.02, xanchor="left", y=1, yanchor="top",
            showarrow=False, align="left", bgcolor="rgba(255, 255, 255, 0.9)"
        )]
    )

    # Axis configurations
    fig.update_yaxes(title_text="Water Depth (mm)", row=1, col=1, rangemode="tozero")
    fig.update_yaxes(title_text="", row=1, col=2)
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Exceedance Prob. (%)", row=1, col=2)

    if save:
        return fig
    else:
        fig.show()


def plot_reservoir_timeseries(
    ts: pd.DataFrame,
    attributes: pd.Series,
    save: bool = False,
    **kwargs
    ):
    """
    Creates an interactive figure with two plots: the time series and the flow duration curve.
    Interactive buttons allow to transform the specific discharge and precipitation data to 
    logarithmic or square root scales to identify issues in the low flows.
    
    Parameters:
    -----------
    ts: pandas.Series
        Discharge time series
    attributes: pd.Series
        Reservoir and dam attributes
    save: boolean
        If True, return an object with the Plotly figure. If false, show the figure
    
    Keyword arguments:
    ------------------
    c_fill: string
        Color used to plot reservoir filling
    c_in: string
        Color used to plot inflow
    c_out: string
        Color used to plot outflow
    c_precip: string
        Color used to plot precipitation
    title: string
        Figure title
    """

    # Extract keywords
    c_fill = kwargs.get('c_fill', 'black')
    c_in = kwargs.get('c_line', 'seagreen')
    c_out = kwargs.get('c_line', 'indianred')
    c_precip = kwargs.get('c_bar', 'steelblue')
    title = kwargs.get('title', None)
    yaxis_pos = kwargs.get('yaxis_pos', 0.06)

    # extract time series
    variables = ['filling', 'inflow_cms', 'inflow_mm', 'outflow_cms', 'outflow_mm', 'precip_mm', 'temp_degC', 'pet_mm']
    missing_vars = set(variables).difference(ts.columns)
    if len(missing_vars) > 0:
        ts[missing_vars] = np.nan

    # 1. Compute hydrological signatures
    _, bfi_outflow = baseflow_index(ts['outflow_cms'])
    fi_outflow = flashiness_index(ts['outflow_cms'])
    fdc_inflow, _ = slope_fdc(ts['inflow_cms'])
    fdc_outflow, slope_outflow = slope_fdc(ts['outflow_cms'])
    fdc_precip, _ = slope_fdc(ts['precip_mm'])

    # Calculate Climatology
    climatology = ts.mean(skipna=True)
    vars = [var for var in climatology.index if var.endswith('_mm')]
    climatology[vars] *= 365 # transform to mm/year

    # Degree of regulation
    dor = attributes.cap_mcm / (climatology.inflow_mm * attributes.catch_skm) * 1e3

    signature_text = (
        "<b>Properties</b><br>"
        f"Capacity: {attributes.cap_mcm:.1f} hm³<br>"
        f"Surface: {attributes.area_skm:.1f} km²<br>"
        f"Catchment: {attributes.catch_skm:.1f} km²<br>"
        f"Deg. Regulation: {dor:.2f}<br>"
        f"Deg. Disruptivity: {attributes.dod_m:.2f} m<br>"
        f"Use: {attributes.main_use}<br>"
        "<br><b>Climatology</b><br>"
        f"Filling: {climatology.filling:.2f}<br>"
        f"Inflow: {climatology.inflow_mm:.0f} mm/year<br>"
        f"Outflow: {climatology.outflow_mm:.0f} mm/year<br>"
        f"Precipitation: {climatology.precip_mm:.0f} mm/year<br>"
        f"PET: {climatology.pet_mm:.0f} mm/year<br>"
        f"Temperature: {climatology.temp_degC:.1f} °C<br>"
        "<br><b>Hydrological Signatures</b>"
        f"<br>Baseflow Index: {bfi_outflow:.2f}<br>"
        f"Flashiness Index: {fi_outflow:.2f}<br>"
        f"Slope FDC: {slope_outflow:.2f}<br>"
    )

    # 2. Create Subplots (Simple single Y-axis)
    fig = make_subplots(
        rows=1, cols=2, 
        shared_yaxes=True,
        column_widths=[0.7, 0.25], 
        horizontal_spacing=0.03,
        subplot_titles=("Hydrograph", "Flow Duration Curve"),
        specs=[[{"secondary_y": True}, {"secondary_y": False}]]
    )

    # 3. Add traces
    # Trace 0: Precipitation (Background)
    fig.add_trace(
        go.Bar(x=ts.index, y=ts['precip_mm'], name="Precipitation", marker_color=c_precip, opacity=0.6, showlegend=True),
        row=1, col=1
    )

    # Trace 1: Inflow
    fig.add_trace(
        go.Scatter(x=ts.index, y=ts['inflow_mm'], name="Inflow", line=dict(color=c_in, width=1), legendgroup="Inflow", showlegend=True),
        row=1, col=1
    )

    # Trace 2: Outflow
    fig.add_trace(
        go.Scatter(x=ts.index, y=ts['outflow_mm'], name="Outflow", line=dict(color=c_out, width=1), legendgroup="Outflow", showlegend=True),
        row=1, col=1,
    )

    # Trace 3: Storage
    fig.add_trace(
        go.Scatter(x=ts.index, y=ts['filling'], name="Filling", line=dict(color=c_fill, width=1), legendgroup="Filling", showlegend=True),
        row=1, col=1, secondary_y=True
    )

    # Trace 4: Flow Duration Curve of Precipitation (Background)
    fig.add_trace(
        go.Scatter(x=fdc_precip.index * 100, y=fdc_precip, name="Precipitation", line=dict(color=c_precip, width=2), opacity=0.6, showlegend=False),
        row=1, col=2
    )

    # Trace 5: Flow Duration Curve of Inflow
    fig.add_trace(
        go.Scatter(x=fdc_inflow.index * 100, y=fdc_inflow.values, name="Inflow", line=dict(color=c_in, width=2), showlegend=False),
        row=1, col=2
    )

    # Trace 6: Flow Duration Curve of Outflow
    fig.add_trace(
        go.Scatter(x=fdc_outflow.index * 100, y=fdc_outflow.values, name="Outflow", line=dict(color=c_out, width=2), showlegend=False),
        row=1, col=2
    )

    # 4. Update Layout & Scale Buttons
    mm_cols = [col for col in ts.columns if col.endswith('_mm')]
    ymax = ts[mm_cols].max().max() * 1.2
    fig.update_layout(
        title_text=f"<b>{title if title else ''}</b>",
        title_x=0.5,
        margin=dict(l=100, r=275, t=100, b=50),
        template="plotly_white",
        height=550,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.35,
            itemclick="toggle",
            itemdoubleclick="toggleothers",
            groupclick="togglegroup",
            bgcolor="rgba(255, 255, 255, 0.5)"
        ),
        updatemenus=[
            # Scale buttons
            dict(
                type="buttons", direction="right", active=0, x=yaxis_pos, xanchor="left", y=1.15,
                buttons=[
                    dict(label="Linear Scale", method="update", 
                         args=[
                             {"y": [ts['precip_mm'], ts['inflow_mm'], ts['outflow_mm'], fdc_precip.values, fdc_inflow.values, fdc_outflow.values]}, 
                             {"yaxis.type": "linear", "yaxis.range": [0, ymax], "yaxis.title.text": "Water Depth (mm)", "yaxis.position": yaxis_pos},
                             # trace indices
                             [0, 1, 2, 4, 5, 6]
                         ]),
                    dict(label="Log Scale", method="update",
                         args=[
                             {"y": [ts['precip_mm'], ts['inflow_mm'], ts['outflow_mm'], fdc_precip.values, fdc_inflow.values, fdc_outflow.values]}, 
                             {"yaxis.type": "log", "yaxis.autorange": True, "yaxis.title.text": "Water Depth (log mm)", "yaxis.position": yaxis_pos},
                             [0, 1, 2, 4, 5, 6]
                         ]),
                    dict(label="Sqrt Scale", method="update",
                         args=[
                             {"y": [ts['precip_mm']**0.5, ts['inflow_mm']**0.5, ts['outflow_mm']**0.5, fdc_precip.values**0.5, fdc_inflow.values**0.5, fdc_outflow.values**0.5]},
                             {"yaxis.type": "linear", "yaxis.range": [0, ymax**0.5], "yaxis.title.text": "Water Depth (√mm)", "yaxis.position": yaxis_pos},
                             [0, 1, 2, 4, 5, 6]
                         ])
                ],
            ),
        ],
        annotations=[dict(
            text=signature_text, xref="paper", yref="paper",
            x=1.02, xanchor="left", y=1, yanchor="top",
            showarrow=False, align="left", bgcolor="rgba(255, 255, 255, 0.9)"
        )]
    )

    # Axis configurations
    fig.update_yaxes(
        title_text="Water Depth (mm)",
        row=1, col=1,
        range=[0, ymax],
        # rangemode='tozero',
        secondary_y=False,
        side="left",
        anchor="x",
        position=yaxis_pos
    )
    fig.update_yaxes(
        title_text="Filling (-)",
        row=1, col=1,
        secondary_y=True,
        range=[0, 1.1],
        showgrid=False,
        side="left",
        anchor="free",
        position=0.0,
        overlaying="y"
    )
    fig.update_yaxes(title_text="", row=1, col=2)
    fig.update_xaxes(title_text="Date", domain=[yaxis_pos, 0.7], row=1, col=1)
    fig.update_xaxes(title_text="Exceedance Prob. (%)", domain=[0.75, 1.0], row=1, col=2)

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

    fig.update_layout(height=None, autosize=True)

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
                    overflow: hidden;
                }}
                .hydrograph {{ flex: 1; min-height: 50vh; width: 100%; }}
                .hydrograph > div {{ height: 100% !important; width: 100% !important; }}
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