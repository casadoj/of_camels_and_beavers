from pathlib import Path
from typing import Optional, Union
import logging

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio


from ocab.plots.utils import compute_annual_timeseries, compute_monthly_climatology, define_y_limits
from ocab.signatures import annual_runoff, baseflow_index, flashiness_index, slope_fdc, budyko

logger = logging.getLogger(__name__)

def plot_stations_map(
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


# def plot_station_timeseries(
#     ts: pd.DataFrame,
#     area: float,
#     regime: Optional[str] = None,
#     save: bool = False,
#     **kwargs
#     ):
#     """
#     Creates an interactive figure with four plots: daily and annual timeseries, the flow 
#     duration curve, and the climograph.
#     Interactive buttons allow to transform the specific discharge and precipitation data to 
#     logarithmic or square root scales to identify issues in the low flows.
    
#     Parameters:
#     -----------
#     ts: pandas.Series
#         Discharge time series
#     area: float
#         Catchment area (km²)
#     regime: string (optional)
#         Flow regime (if provided by the Ministry)
#     save: boolean
#         If True, return an object with the Plotly figure. If false, show the figure
    
#     Keyword arguments:
#     ------------------
#     alpha: float
#         Transparency of the precipitation bar plots
#     c_dis: string
#         Color used to plot discharge
#     c_precip: string
#         Color used to plot precipitation
#     title: string
#         Figure title
#     """

#     # Extract keywords
#     alpha = kwargs.get('alpha', 0.2)
#     c_dis = kwargs.get('c_dis', 'darkslategrey')
#     c_precip = kwargs.get('c_precip', 'lightblue')
#     c_temp = kwargs.get('c_temp', 'darkred')
#     title = kwargs.get('title', None)

#     # Setup Grid
#     fig = make_subplots(
#         rows=4, cols=2,
#         specs=[
#             [{"colspan": 2}, None], # row 1
#             [{"colspan": 2}, None], # row 2
#             [{"colspan": 2, "secondary_y": True}, None], # row 3
#             [{"secondary_y": True}, {}] # row 4
#             ],
#         column_widths=[0.5, 0.5], 
#         row_heights=[0.48, 0.02, 0.1, 0.4],
#         shared_xaxes=False,
#         shared_yaxes=False,
#         subplot_titles=("", "", "", 'Climatology', "Flow Duration Curve"),
#         vertical_spacing=0.05,
#         horizontal_spacing=0.15
#     )

#     # --- PLOT 1: DAILY TIME SERIES ---

#     row, col = 1, 1

#     # add traces
#     fig.add_trace(
#         go.Bar(
#             x=ts.index, 
#             y=ts['precip_mm'], 
#             name="Precipitation", 
#             marker_color=c_precip, 
#             opacity=1 - alpha,
#             marker_line_width=0,
#             legendgroup="Precipitation",
#             showlegend=False
#         ),
#         row=row, col=col
#     )
#     fig.add_trace(
#         go.Scatter(
#             x=ts.index, 
#             y=ts['discharge_mm'], 
#             name="Discharge", 
#             line=dict(color=c_dis, width=1), 
#             legendgroup="Q",
#             showlegend=False
#         ),
#         row=row, col=col
#     )

#     # set axes properties
#     fig.update_yaxes(
#         title_text="mm", 
#         rangemode='nonnegative',
#         row=row, col=col, secondary_y=False
#     )

#     # --- PLOT 2: MISSING DATA ---

#     row, col = 2, 1

#     # find missing discharge dates
#     missing_x = ts[ts['discharge_cms'].isnull()].index
#     missing_y = [0] * len(missing_x)
#     fig.add_trace(
#         go.Scatter(
#             x=missing_x,
#             y=missing_y, 
#             mode='markers',
#             marker=dict(
#                 symbol='line-ns-open',
#                 size=10,
#                 color=c_dis,
#                 line_width=1
#             ),
#             legendgroup="Q",
#             showlegend=False,
#             hoverinfo='x'
#         ),
#         row=row, col=col
#     )

#     # set axes
#     fig.update_yaxes(
#         showgrid=False, 
#         showticklabels=False, 
#         zeroline=False, 
#         fixedrange=True,
#         row=row, col=col
#     )
#     fig.update_xaxes(
#         showgrid=False, 
#         showticklabels=False, 
#         row=row, col=col,
#         matches='x'
#     )

#     # --- PLOT 3: ANNUAL TIME SERIES ---

#     row, col = 3, 1

#     # compute annual time series
#     ts_y = compute_annual_timeseries(ts)

#     # add traces
#     fig.add_trace(
#         go.Bar(
#             x=ts_y.index, 
#             y=ts_y['precip_mm'], 
#             name="Precipitation", 
#             marker_color=c_precip, 
#             opacity=1 - alpha,
#             legendgroup="Precipitation",
#             showlegend=True
#         ),
#         row=row, col=col
#     )
#     fig.add_trace(go.Scatter(
#             x=ts_y.index, 
#             y=ts_y['temp_degC'], 
#             name="Temperature",
#             line=dict(color=c_temp, width=2),
#             legendgroup="Temperature",
#             showlegend=True
#         ), 
#         row=row, col=col, secondary_y=True
#     )
#     fig.add_trace(
#         go.Scatter(
#             x=ts_y.index, 
#             y=ts_y['discharge_mm'], 
#             name="Discharge",
#             line=dict(color=c_dis, width=2),
#             legendgroup="Q",
#             showlegend=True
#         ),
#         row=row, col=col
#     )

#     # set axes properties
#     scale_y = 100
#     round_mm_y = 500
#     mm_range_y, deg_range_y = define_y_limits(ts_y, round_mm_y, scale_y)
#     fig.update_yaxes(
#         title_text="mm", 
#         range=mm_range_y, 
#         dtick=round_mm_y, 
#         row=row, col=col
#     )
#     fig.update_yaxes(
#         title_text="°C", 
#         range=deg_range_y, 
#         dtick=round_mm_y / scale_y, 
#         row=row, col=col, secondary_y=True
#     )
#     fig.update_xaxes(
#         showticklabels=False, 
#         row=row, col=col,
#         matches='x'
#     )

#     # --- PLOT 4: CLIMOGRAPH ---

#     row, col = 4, 1

#     # compute monthly climatology
#     ts_m = compute_monthly_climatology(ts)

#     # add traces
#     fig.add_trace(
#         go.Bar(
#             x=ts_m.index, 
#             y=ts_m['precip_mm'], 
#             name="Precipitation", 
#             marker_color=c_precip, 
#             opacity=1 - alpha,
#             legendgroup="Precipitation",
#             showlegend=False
#         ), 
#         row=row, col=col
#     )
#     fig.add_trace(
#         go.Scatter(
#             x=ts_m.index, 
#             y=ts_m['temp_degC'], 
#             name="Temperature", 
#             line=dict(color=c_temp, width=2),
#             legendgroup="Temperature",
#             showlegend=False
#         ),
#         row=row, col=col, secondary_y=True
#     )
#     fig.add_trace(
#         go.Scatter(
#             x=ts_m.index, 
#             y=ts_m['discharge_mm'], 
#             name="Discharge", 
#             line=dict(color=c_dis, width=2),
#             legendgroup="Q",
#             showlegend=False
#         ), 
#         row=row, col=col
#     )

#     # set axes properties
#     scale_m = 2
#     round_mm_m = 20
#     mm_range_m, deg_range_m = define_y_limits(ts_m, round_mm_m, scale_m)
#     fig.update_yaxes(
#         title_text="mm", 
#         range=mm_range_m, 
#         dtick=round_mm_m, 
#         row=row, col=col
#     )
#     fig.update_yaxes(
#         title_text="°C", 
#         range=deg_range_m, 
#         dtick=round_mm_m / scale_m, 
#         row=row, col=col, secondary_y=True
#     )
#     fig.update_xaxes(
#         tickvals=list(range(1, 13)), 
#         ticktext=['J','F','M','A','M','J','J','A','S','O','N','D'], 
#         row=row, col=col
#     )

#     # --- PLOT 5: FLOW DURATION CURVE ---

#     row, col = 4, 2

#     # compute flow duration curve
#     fdc_precip, _ = slope_fdc(ts['precip_mm'])
#     fdc_dis, slope = slope_fdc(ts['discharge_mm'])

#     # add traces
#     fig.add_trace(
#         go.Scatter(
#             x=fdc_precip.index * 100, 
#             y=fdc_precip, 
#             name="Precipitation", 
#             line=dict(color=c_precip, width=2), 
#             showlegend=False,
#             legendgroup="Precipitation"
#         ),
#         row=row, col=col
#     )
#     fig.add_trace(
#         go.Scatter(
#             x=fdc_dis.index * 100, 
#             y=fdc_dis.values, 
#             name="Discharge", 
#             line=dict(color=c_dis, width=2), 
#             showlegend=False,
#             legendgroup="Q"
#         ),
#         row=row, col=col
#     ) 

#     # set axes
#     fig.update_xaxes(title_text="Exceedance Prob. (%)", row=row, col=col)
#     fig.update_yaxes(
#         title_text="mm", 
#         rangemode='nonnegative',
#         row=row, col=col
#     )

#     ### --- SIGNATURES & CLIMATOLOGY VALUES ---

#     # Compute hydrological signatures
#     avg_dis = annual_runoff(ts['discharge_cms'], area)
#     _, bfi = baseflow_index(ts['discharge_cms'])
#     fi = flashiness_index(ts['discharge_cms'])

#     # Calculate climatology values
#     avg_precip = ts['precip_mm'].mean()
#     avg_temp = ts['temp_degC'].mean()
#     avg_pet = ts['pet_mm'].mean()

#     signature_text = (
#         "<b>Catchment Properties</b><br>"
#         f"Area: {area:.0f} km²<br>"
#         f"Regime: {regime}<br>"
#         "<br><b>Climatology</b><br>"
#         f"Discharge: {avg_dis:.0f} mm/year<br>"
#         f"Precipitation: {avg_precip * 365:.0f} mm/year<br>"
#         f"PET: {avg_pet * 365:.0f} mm/year<br>"
#         f"Temperature: {avg_temp:.1f} °C<br>"
#         "<br><b>Hydrological Signatures</b>"
#         f"<br>Baseflow Index: {bfi:.2f}<br>"
#         f"Flashiness Index: {fi:.2f}<br>"
#         f"Slope FDC: {slope:.2f}<br>"
#     )

#     # Update Layout & Scale Buttons
#     y_raw = [
#         ts['precip_mm'], ts['discharge_mm'], 
#         missing_y,
#         ts_y['precip_mm'], ts_y['temp_degC'], ts_y['discharge_mm'],
#         ts_m['precip_mm'], ts_m['temp_degC'],  ts_m['discharge_mm'],
#         fdc_precip.values, fdc_dis.values,
#     ]
#     sqrt_traces = [0, 1, 9, 10]
#     y_sqrt = [trace**.5 if i in sqrt_traces else trace for i, trace in enumerate(y_raw)]
#     fig.update_layout(
#         title_text=f"<b>{title if title else ''}</b>",
#         title_x=0.5,
#         margin=dict(l=50, r=200, t=50, b=50),
#         template="plotly_white",
#         autosize=True,
#         showlegend=True,
#         legend=dict(
#             orientation="h",
#             yanchor="top",
#             y=-0.075,
#             xanchor="center",
#             x=0.45
#         ),
#         bargap=0.08, 
#         barmode='overlay',
#         updatemenus=[
#             dict(
#                 type="buttons", direction="down", active=0, x=1.02, xanchor="left", y=0, yanchor='bottom', showactive=True,
#                 buttons=[
#                     dict(label="Linear Scale", method="update", 
#                          args=[
#                              {"y": y_raw},
#                              {
#                                  "yaxis.type": "linear", "yaxis.title.text": "mm",
#                                  "yaxis7.type": "linear", "yaxis7.title.text": "mm",
#                             }
#                          ]),
#                     dict(label="Log Scale", method="update",
#                          args=[
#                              {"y": y_raw}, 
#                              {
#                                  "yaxis.type": "log", "yaxis.title.text": "log mm",
#                                  "yaxis7.type": "log", "yaxis7.title.text": "log mm",
#                              }
#                          ]),
#                     dict(label="Sqrt Scale", method="update",
#                          args=[
#                              {"y": y_sqrt},
#                              {
#                                  "yaxis.type": "linear", "yaxis.title.text": "sqrt mm",
#                                  "yaxis7.type": "linear", "yaxis7.title.text": "sqrt mm",
#                              }
#                          ])
#                 ],
#             )
#         ],
#     )
#     fig.add_annotation(
#         text=signature_text, 
#         xref="paper", x=1.02, xanchor="left", 
#         yref="paper", y=1, yanchor="top",
#         showarrow=False, align="left", bgcolor="rgba(255, 255, 255, 0.9)"
#     )
#     fig.update_xaxes(
#         range=[ts.index.min(), ts.index.max()],
#         row=1, col=1
#     )

#     if save:
#         return fig
#     else:
#         fig.show()


def plot_station_timeseries(
    ts: pd.DataFrame,
    area: float,
    regime: Optional[str] = None,
    save: bool = False,
    **kwargs
    ):
    """
    Creates an interactive figure with four plots: daily and annual timeseries, the flow 
    duration curve, and the climograph.
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
    alpha: float
        Transparency of the precipitation bar plots
    c_dis: string
        Color used to plot discharge
    c_precip: string
        Color used to plot precipitation
    title: string
        Figure title
    """

    # Extract keywords
    alpha = kwargs.get('alpha', 0.2)
    c_dis = kwargs.get('c_dis', 'darkslategrey')
    c_precip = kwargs.get('c_precip', 'lightblue')
    c_temp = kwargs.get('c_temp', 'darkred')
    c_pet = kwargs.get('c_pet', 'darkseagreen') #'olivedrab')
    title = kwargs.get('title', None)

    # Setup Grid
    fig = make_subplots(
        rows=4, cols=2,
        specs=[
            [{"colspan": 2}, None], # row 1
            [{"colspan": 2}, None], # row 2
            [{"colspan": 2, "secondary_y": True}, None], # row 3
            [{"secondary_y": True}, {}] # row 4
            ],
        column_widths=[0.5, 0.5], 
        row_heights=[0.48, 0.02, 0.1, 0.4],
        shared_xaxes=False,
        shared_yaxes=False,
        subplot_titles=("", "", "", 'Climatology', "Budyko Diagram"),
        vertical_spacing=0.05,
        horizontal_spacing=0.15
    )

    # --- PLOT 1: DAILY TIME SERIES ---

    row, col = 1, 1

    # add traces
    fig.add_trace(
        go.Bar(
            x=ts.index, 
            y=ts['precip_mm'], 
            name="Precipitation", 
            marker_color=c_precip, 
            opacity=1 - alpha,
            marker_line_width=0,
            legendgroup="P",
            showlegend=False
        ),
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts.index, 
            y=ts['discharge_mm'], 
            name="Discharge", 
            line=dict(color=c_dis, width=1), 
            legendgroup="Q",
            showlegend=False
        ),
        row=row, col=col
    )

    # set axes properties
    fig.update_yaxes(
        title_text="mm", 
        rangemode='nonnegative',
        row=row, col=col, secondary_y=False
    )

    # --- PLOT 2: MISSING DATA ---

    row, col = 2, 1

    # find missing discharge dates
    missing_x = ts[ts['discharge_cms'].isnull()].index
    missing_y = [0] * len(missing_x)
    fig.add_trace(
        go.Scatter(
            x=missing_x,
            y=missing_y, 
            mode='markers',
            marker=dict(
                symbol='line-ns-open',
                size=10,
                color=c_dis,
                line_width=1
            ),
            legendgroup="Q",
            showlegend=False,
            hoverinfo='x'
        ),
        row=row, col=col
    )

    # set axes
    fig.update_yaxes(
        showgrid=False, 
        showticklabels=False, 
        zeroline=False, 
        fixedrange=True,
        row=row, col=col
    )
    fig.update_xaxes(
        showgrid=False, 
        showticklabels=False, 
        row=row, col=col,
        matches='x'
    )

    # --- PLOT 3: ANNUAL TIME SERIES ---

    row, col = 3, 1

    # compute annual time series
    ts_y = compute_annual_timeseries(ts, rule='YS-OCT')

    # add traces
    fig.add_trace(
        go.Bar(
            x=ts_y.index, 
            y=ts_y['precip_mm'], 
            name="Precipitation", 
            marker_color=c_precip, 
            opacity=1 - alpha,
            legendgroup="P",
            showlegend=True
        ),
        row=row, col=col
    )
    fig.add_trace(go.Scatter(
            x=ts_y.index, 
            y=ts_y['temp_degC'], 
            name="Temperature",
            line=dict(color=c_temp, width=2),
            legendgroup="T",
            showlegend=True
        ), 
        row=row, col=col, secondary_y=True
    )
    fig.add_trace(go.Scatter(
            x=ts_y.index, 
            y=ts_y['pet_mm'], 
            name="PET",
            line=dict(color=c_pet, width=2),
            legendgroup="PET",
            showlegend=True
        ), 
        row=row, col=col,
    )
    fig.add_trace(
        go.Scatter(
            x=ts_y.index, 
            y=ts_y['discharge_mm'], 
            name="Discharge",
            line=dict(color=c_dis, width=2),
            legendgroup="Q",
            showlegend=True
        ),
        row=row, col=col
    )

    # set axes properties
    scale_y = 100
    round_mm_y = 500
    mm_range_y, deg_range_y = define_y_limits(ts_y, round_mm_y, scale_y)
    fig.update_yaxes(
        title_text="mm", 
        range=mm_range_y, 
        dtick=round_mm_y, 
        row=row, col=col
    )
    fig.update_yaxes(
        title_text="°C", 
        range=deg_range_y, 
        dtick=round_mm_y / scale_y, 
        row=row, col=col, secondary_y=True
    )
    fig.update_xaxes(
        showticklabels=False, 
        row=row, col=col,
        matches='x'
    )

    # --- PLOT 4: CLIMOGRAPH ---

    row, col = 4, 1

    # compute monthly climatology
    ts_m = compute_monthly_climatology(ts)

    # add traces
    fig.add_trace(
        go.Bar(
            x=ts_m.index, 
            y=ts_m['precip_mm'], 
            name="Precipitation", 
            marker_color=c_precip, 
            opacity=1 - alpha,
            legendgroup="P",
            showlegend=False
        ), 
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts_m.index, 
            y=ts_m['temp_degC'], 
            name="Temperature", 
            line=dict(color=c_temp, width=2),
            legendgroup="T",
            showlegend=False
        ),
        row=row, col=col, secondary_y=True
    )
    fig.add_trace(
        go.Scatter(
            x=ts_m.index, 
            y=ts_m['pet_mm'], 
            name="PET", 
            line=dict(color=c_pet, width=2),
            legendgroup="PET",
            showlegend=False
        ),
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts_m.index, 
            y=ts_m['discharge_mm'], 
            name="Discharge", 
            line=dict(color=c_dis, width=2),
            legendgroup="Q",
            showlegend=False
        ), 
        row=row, col=col
    )

    # set axes properties
    scale_m = 2
    round_mm_m = 20
    mm_range_m, deg_range_m = define_y_limits(ts_m, round_mm_m, scale_m)
    fig.update_yaxes(
        title_text="mm", 
        range=mm_range_m, 
        dtick=round_mm_m, 
        row=row, col=col
    )
    fig.update_yaxes(
        title_text="°C", 
        range=deg_range_m, 
        dtick=round_mm_m / scale_m, 
        row=row, col=col, secondary_y=True
    )
    fig.update_xaxes(
        tickvals=list(range(1, 13)), 
        ticktext=['J','F','M','A','M','J','J','A','S','O','N','D'], 
        row=row, col=col
    )

    # --- PLOT 5: BUDYKO DIAGRAM ---

    row, col = 4, 2

    # calculate data
    aridity = ts_y['pet_mm'] / ts_y['precip_mm']
    evaporativity = (ts_y['precip_mm'] - ts_y['discharge_mm']) / ts_y['precip_mm']

    # plot limits
    round = 0.2
    xlim = [0, max(1.4, np.ceil(aridity.max() / round) * round)]
    ylim = [0, 1.4]

    # Theoretical lines
    line_props = dict(color='grey', width=1)
    # Water Limit
    fig.add_trace(
        go.Scatter(
            x=np.linspace(*xlim, 100), 
            y=[1] * 100, 
            mode='lines', 
            name='Water Limit',
            line=line_props, 
            showlegend=False,
            hovertemplate=" "
        ),
        row=row, col=col
    )
    # Energy Limit
    fig.add_trace(
        go.Scatter(
            x=np.linspace(*xlim, 100), 
            y=np.linspace(*xlim, 100), 
            mode='lines', 
            name='Energy Limit',
            line=line_props, 
            showlegend=False,
            hovertemplate=" "
        ),
        row=row, col=col
    )
    # Budyko Curve
    aridity_idx = np.linspace(0.001, xlim[1], 100)
    fig.add_trace(
        go.Scatter(
            x=aridity_idx, 
            y=budyko(aridity_idx, n=2), 
            mode='lines', 
            name='Budyko Limit',
            line=line_props,
            showlegend=False,
            hovertemplate=" "
        ),
        row=row, col=col
    )

    # Add annual values
    fig.add_trace(
        go.Scatter(
            x=aridity, 
            y=evaporativity,
            mode='markers',
            name='Budyko',
            marker=dict(color='sienna', size=8, line=dict(width=1, color='white')),
            customdata=ts_y.index.year,
            hovertemplate="<b>Year: %{customdata}</b><br>Arid. Index: %{x:.2f}<br>Evap. Index: %{y:.2f}<extra></extra>",
            showlegend=False
        ),
        row=row, col=col
    )

    # set axes
    fig.update_xaxes(
        title_text="Aridity Index: PET/P", 
        range=xlim,
        row=row, col=col)
    fig.update_yaxes(
        title_text="Evaporative Index: (P-Q)/P", 
        range=ylim,
        row=row, col=col
    )

    ### --- SIGNATURES & CLIMATOLOGY VALUES ---

    # Compute hydrological signatures
    avg_dis = annual_runoff(ts['discharge_cms'], area)
    _, bfi = baseflow_index(ts['discharge_cms'])
    fi = flashiness_index(ts['discharge_cms'])
    fdc_dis, slope = slope_fdc(ts['discharge_mm'])

    # Calculate climatology values
    avg_precip = ts['precip_mm'].mean()
    avg_temp = ts['temp_degC'].mean()
    avg_pet = ts['pet_mm'].mean()

    signature_text = (
        "<b>Catchment Properties</b><br>"
        f"Area: {area:.0f} km²<br>"
        f"Regime: {regime}<br>"
        "<br><b>Climatology</b><br>"
        f"Discharge: {avg_dis:.0f} mm/year<br>"
        f"Precipitation: {avg_precip * 365:.0f} mm/year<br>"
        f"PET: {avg_pet * 365:.0f} mm/year<br>"
        f"Temperature: {avg_temp:.1f} °C<br>"
        "<br><b>Hydrological Signatures</b>"
        f"<br>Baseflow Index: {bfi:.2f}<br>"
        f"Flashiness Index: {fi:.2f}<br>"
        f"Slope FDC: {slope:.2f}<br>"
    )

    # Update Layout & Scale Buttons
    y_raw = [ts['precip_mm'], ts['discharge_mm']]
    y_sqrt = [trace**.5 for trace in y_raw]
    fig.update_layout(
        title_text=f"<b>{title if title else ''}</b>",
        title_x=0.5,
        margin=dict(l=50, r=200, t=50, b=50),
        template="plotly_white",
        autosize=True,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.075,
            xanchor="center",
            x=0.45
        ),
        bargap=0.08, 
        barmode='overlay',
        updatemenus=[
            dict(
                # type="buttons", direction="down", active=0, x=1.02, xanchor="left", y=0, yanchor='bottom', showactive=True,
                type="buttons", direction="down", active=0, x=1.02, xanchor="left", y=1, yanchor='top', showactive=True,
                buttons=[
                    dict(label="Linear Scale", method="update", 
                         args=[
                             {"y": y_raw},
                             {"yaxis.type": "linear", "yaxis.title.text": "mm"},
                             [0, 1]
                         ]),
                    dict(label="Log Scale", method="update",
                         args=[
                             {"y": y_raw}, 
                             {"yaxis.type": "log", "yaxis.title.text": "log mm"},
                             [0, 1]
                         ]),
                    dict(label="Sqrt Scale", method="update",
                         args=[
                             {"y": y_sqrt},
                             {"yaxis.type": "linear", "yaxis.title.text": "sqrt mm"},
                             [0, 1]
                         ])
                ],
            )
        ],
    )
    fig.add_annotation(
        text=signature_text, 
        xref="paper", x=1.02, xanchor="left", 
        yref="paper", y=0, yanchor="bottom",
        showarrow=False, align="left", bgcolor="rgba(0, 0, 0, 0)"
    )
    fig.update_xaxes(
        range=[ts.index.min(), ts.index.max()],
        row=1, col=1
    )

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
        Result of `plot_reservoir_timeseries()`
    path: string
        Name of the HTML file where the figure wil be saved
    start: string
        Start date of the time series. Format YYYY-mm-dd
    end: string
        End date of the time series. Format YYYY-mm-dd
    """
        
    fig.update_layout(height=None, width=None, autosize=True)

    # Convert figure to HTML div string
    plotly_html = pio.to_html(
        fig, 
        full_html=False, 
        include_plotlyjs='cdn',
        include_mathjax=False,
        config={'responsive': True, 'displaylogo': False}
    )

    full_page_html = f"""
        <html>
        <head>
            <meta charset="utf-8" />
            <style>
                body {{ 
                    margin: 0; padding: 0; height: 100vh; width: 100vw;
                    display: flex; 
                    flex-direction: row; 
                    font-family: sans-serif;
                    overflow: hidden;
                }}
                .hydrograph {{ 
                    flex: 7; 
                    height: 100vh; 
                    min-width: 0;
                    position: relative; /* Added to anchor the button */
                }}
                .google-form {{ 
                    flex: 3; 
                    height: 100vh; 
                    border-left: 1px solid #ddd;
                    display: flex;
                }}
                .hydrograph > .plotly-graph-div {{ height: 100% !important; width: 100% !important; }}
                
                iframe {{ width: 100%; height: 100%; border: none; }}
                
                /* Updated: Positioned at bottom right of the plot panel */
                .back-nav {{ 
                    position: absolute; 
                    bottom: 20px; 
                    right: 20px; 
                    z-index: 9999; 
                }}
                .back-btn {{
                    text-decoration: none; 
                    color: white; 
                    font-size: 14px; 
                    font-weight: bold; 
                    background-color: steelblue; /* Solid color looks better at bottom */
                    padding: 10px 16px; 
                    border-radius: 5px; 
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    transition: background-color 0.3s;
                }}
                .back-btn:hover {{
                    background-color: #2e5d86;
                }}
            </style>
        </head>
        <body>
            <div class="hydrograph">
                <div class="back-nav">
                    <a href="../../../index.html" class="back-btn">← Back to map</a>
                </div>
                {plotly_html}
            </div>
            
            <div class="google-form" id="form-container"></div>

            <script>
                (function() {{
                    const baseUrl = "https://docs.google.com/forms/d/e/1FAIpQLSdMDms_IAwkhPwOVqLvU0oVghG9Xti1LMhTsPoujm2w2uXF9A/viewform?embedded=true";
                    const emailEntryId = "2010975770";
                    const stationEntryId = "1301492004";
                    const startEntry1Id = "598747998";
                    const endEntry1Id = "2001326573";
                    const startEntry2Id = "1136531299";
                    const endEntry2Id = "530564783";

                    const userEmail = localStorage.getItem('userEmail') || "";
                    const filename = window.location.pathname.split('/').pop();
                    const stationId = filename.replace('.html', '');
                    const start = "{start}";
                    const end = "{end}";

                    const finalUrl = baseUrl + 
                        "&entry." + stationEntryId + "=" + stationId + 
                        "&entry." + emailEntryId + "=" + encodeURIComponent(userEmail) + 
                        "&entry." + startEntry1Id + "=" + start + 
                        "&entry." + endEntry1Id + "=" + end +
                        "&entry." + startEntry2Id + "=" + start + 
                        "&entry." + endEntry2Id + "=" + end;

                    document.getElementById('form-container').innerHTML = 
                        '<iframe src="' + finalUrl + '" frameborder="0">Loading form…</iframe>';
                }})();

                window.addEventListener('load', function() {{
                    setTimeout(function() {{ window.dispatchEvent(new Event('resize')); }}, 200); 
                }});
            </script>
        </body>
        </html>
        """
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(full_page_html)