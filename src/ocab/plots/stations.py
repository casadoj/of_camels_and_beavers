import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from typing import Optional

from ocab.plots.utils import compute_annual_timeseries, compute_monthly_climatology
from ocab.signatures import annual_runoff, baseflow_index, flashiness_index, slope_fdc


def _define_y_limits(
        df: pd.DataFrame,
        scale: float,
        round_mm: int,
        cols_mm: list = ['precip_mm', 'discharge_mm'],
        cols_deg: list = ['temp_degC']
):
    """
    """
    
    round_deg = round_mm / scale
    eps = round_mm / 10

    # extract values
    mm_vals = df[cols_mm].values.flatten()
    mm_vals = mm_vals[~np.isnan(mm_vals)]

    deg_vals = df[cols_deg].values.flatten()
    deg_vals = deg_vals[~np.isnan(deg_vals)]

    # Default values if no data exists to prevent crashes
    mm_max_raw = np.nanmax(mm_vals) if mm_vals.size > 0 else 100
    deg_min_raw = np.nanmin(deg_vals) if deg_vals.size > 0 else 0
    deg_max_raw = np.nanmax(deg_vals) if deg_vals.size > 0 else 30

    # get independent min/max values
    mm_min = 0.0
    mm_max = np.ceil(mm_max_raw / round_mm) * round_mm
    deg_min = np.floor(deg_min_raw / round_deg) * round_deg
    deg_max = np.ceil(deg_max_raw / round_deg) * round_deg

    # Sync the scales
    mm_max = max(mm_max, deg_max * scale) + eps
    mm_min = min(mm_min, deg_min * scale) - eps
    deg_max = mm_max / scale
    deg_min = mm_min / scale

    return [mm_min, mm_max], [deg_min, deg_max]

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
    c_dis = kwargs.get('c_dis', 'dimgrey')
    c_precip = kwargs.get('c_precip', 'lightblue')
    c_temp = kwargs.get('c_temp', 'darkred')
    title = kwargs.get('title', None)

    # 1. Setup Grid
    fig = make_subplots(
        rows=4, cols=2,
        specs=[
            [{"colspan": 2, "secondary_y": True}, None], # row 1
            [{"colspan": 2}, None], # row 2
            [{"colspan": 2, "secondary_y": True}, None], # row 3
            [{"secondary_y": True}, {}] # row 4
            ],
        column_widths=[0.5, 0.5], 
        row_heights=[0.48, 0.02, 0.1, 0.4],
        shared_xaxes=False,
        shared_yaxes=False,
        subplot_titles=(
            "", 
            "",
            '', 
            'Climatology',
            "Flow Duration Curve", 
        ),
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
            legendgroup="Precipitation",
            showlegend=True
        ),
        row=row, col=col
    )
    fig.add_trace(go.Scatter(
            x=ts.index, 
            y=ts['temp_degC'], 
            name="Temperature", 
            line=dict(color=c_temp, width=0.7),
            legendgroup="Temperature",
            showlegend=True
        ), 
        row=row, col=col, secondary_y=True
    )
    fig.add_trace(
        go.Scatter(
            x=ts.index, 
            y=ts['discharge_mm'], 
            name="Discharge", 
            line=dict(color=c_dis, width=1), 
            legendgroup="Discharge",
            showlegend=True
        ),
        row=row, col=col
    )

    # set axes properties
    scale = 4
    round_mm_d = 20
    mm_range_d, deg_range_d = _define_y_limits(ts, scale, round_mm_d)
    fig.update_yaxes(
        title_text="mm", 
        range=mm_range_d, 
        dtick=round_mm_d, 
        row=1, col=1, secondary_y=False
    )
    fig.update_yaxes(
        title_text="°C", 
        range=deg_range_d, 
        dtick=round_mm_d / scale, 
        row=1, col=1, secondary_y=True
    )
    fig.add_hline(
        y=0, 
        line_width=0.5, 
        line_color="black", 
        layer="above",
        row=1, col=1
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
                size=12,
                color='gray',
                line_width=1.5
            ),
            name="Missing Data",
            legendgroup="Missing",
            showlegend=True,
            hoverinfo='x'
        ),
        row=row, col=col
    )

    # set axes
    fig.update_yaxes(
        showgrid=False, 
        showticklabels=False, 
        zeroline=False, 
        fixedrange=True, # Prevents vertical zooming on the rug
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
    ts_y = compute_annual_timeseries(ts).round(0)

    # add traces
    fig.add_trace(
        go.Bar(
            x=ts_y.index, 
            y=ts_y['precip_mm'], 
            name="Precipitation", 
            marker_color=c_precip, 
            opacity=1 - alpha,
            legendgroup="Precipitation",
            showlegend=False
        ),
        row=row, col=col
    )
    fig.add_trace(go.Scatter(
            x=ts_y.index, 
            y=ts_y['temp_degC'], 
            name="Temperature",
            line=dict(color=c_temp, width=2),
            legendgroup="Temperature",
            showlegend=False
        ), 
        row=row, col=col, secondary_y=True
    )
    fig.add_trace(
        go.Scatter(
            x=ts_y.index, 
            y=ts_y['discharge_mm'], 
            name="Discharge",
            line=dict(color=c_dis, width=2),
            legendgroup="Discharge",
            showlegend=False
        ),
        row=row, col=col
    )

    # set axes properties
    scale = 100
    round_mm_y = 500
    mm_range_y, deg_range_y = _define_y_limits(ts_y, scale, round_mm_y)
    fig.update_yaxes(
        title_text="mm", 
        range=mm_range_y, 
        dtick=round_mm_y, 
        row=row, col=col
    )
    fig.update_yaxes(
        title_text="°C", 
        range=deg_range_y, 
        dtick=round_mm_y / scale, 
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
    ts_m = compute_monthly_climatology(ts).round(0)

    # add traces
    fig.add_trace(
        go.Bar(
            x=ts_m.index, 
            y=ts_m['precip_mm'], 
            name="Precipitation", 
            marker_color=c_precip, 
            opacity=1 - alpha,
            legendgroup="Precipitation",
            showlegend=False
        ), 
        row=row, col=col
    )
    fig.add_trace(go.Scatter(
            x=ts_m.index, 
            y=ts_m['temp_degC'], 
            name="Temperature", 
            line=dict(color=c_temp, width=2),
            legendgroup="Temperature",
            showlegend=False
        ),
        row=row, col=col, secondary_y=True
    )
    fig.add_trace(
        go.Scatter(
            x=ts_m.index, 
            y=ts_m['discharge_mm'], 
            name="Discharge", 
            line=dict(color=c_dis, width=2),
            legendgroup="Discharge",
            showlegend=False
        ), 
        row=row, col=col
    )

    # set axes properties
    scale = 2
    round_mm_m = 20
    mm_range_m, deg_range_m = _define_y_limits(ts_m, scale, round_mm_m)
    fig.update_yaxes(
        title_text="mm", 
        range=mm_range_m, 
        dtick=round_mm_m, 
        row=row, col=col
    )
    fig.update_yaxes(
        title_text="°C", 
        range=deg_range_m, 
        dtick=round_mm_m / scale, 
        row=row, col=col, secondary_y=True
    )
    fig.update_xaxes(
        tickvals=list(range(1, 13)), 
        ticktext=['J','F','M','A','M','J','J','A','S','O','N','D'], 
        row=row, col=col
    )

    # --- PLOT 5: FLOW DURATION CURVE ---

    row, col = 4, 2

    # compute flow duration curve
    fdc_precip, _ = slope_fdc(ts['precip_mm'])
    fdc_dis, slope = slope_fdc(ts['discharge_mm'])

    # add traces
    fig.add_trace(
        go.Scatter(
            x=fdc_precip.index * 100, 
            y=fdc_precip, 
            name="Precipitation", 
            line=dict(color=c_precip, width=2), 
            showlegend=False,
            legendgroup="Precipitation"
        ),
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=fdc_dis.index * 100, 
            y=fdc_dis.values, 
            name="Discharge", 
            line=dict(color=c_dis, width=2), 
            showlegend=False,
            legendgroup="Discharge"
        ),
        row=row, col=col
    ) 

    # set axes
    fig.update_xaxes(title_text="Exceedance Prob. (%)", row=row, col=col)
    fig.update_yaxes(
        title_text="mm", 
        range=[-round_mm_d / 10, mm_range_d[1]], 
        dtick=round_mm_d, 
        row=row, col=col
    )

    ### --- SIGNATURES & CLIMATOLOGY VALUES ---

    # 1. Compute hydrological signatures
    avg_dis = annual_runoff(ts['discharge_cms'], area)
    _, bfi = baseflow_index(ts['discharge_cms'])
    fi = flashiness_index(ts['discharge_cms'])

    # Calculate Climatology values
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

    # 4. Update Layout & Scale Buttons
    fig.update_layout(
        title_text=f"<b>{title if title else ''}</b>",
        title_x=0.5,
        # margin=dict(l=50, r=275, t=100, b=50),
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
                type="buttons", direction="down", active=0, x=1.02, xanchor="left", y=0, yanchor='bottom', showactive=True,
                buttons=[
                    dict(label="Linear Scale", method="update", 
                         args=[
                             {"y": [
                                 ts['precip_mm'], ts['temp_degC'], ts['discharge_mm'], 
                                 missing_y,
                                 ts_y['precip_mm'], ts_y['temp_degC'], ts_y['discharge_mm'],
                                 ts_m['precip_mm'], ts_m['temp_degC'],  ts_m['discharge_mm'],
                                 fdc_precip.values, fdc_dis.values,
                             ]},
                             {
                                 "yaxis.type": "linear", "yaxis.title.text": "mm",
                                 "yaxis8.type": "linear", "yaxis8.title.text": "mm",
                            }
                         ]),
                    dict(label="Log Scale", method="update",
                         args=[
                             {"y": [
                                 ts['precip_mm'], ts['temp_degC'], ts['discharge_mm'], 
                                 missing_y,
                                 ts_y['precip_mm'], ts_y['temp_degC'], ts_y['discharge_mm'],
                                 ts_m['precip_mm'], ts_m['temp_degC'], ts_m['discharge_mm'],
                                 fdc_precip.values, fdc_dis.values,
                            ]}, 
                             {
                                 "yaxis.type": "log", "yaxis.title.text": "log mm",
                                 "yaxis8.type": "log", "yaxis8.title.text": "log mm",
                             }
                         ]),
                    dict(label="Sqrt Scale", method="update",
                         args=[
                             {"y": [
                                 ts['precip_mm']**0.5, ts['temp_degC'], ts['discharge_mm']**0.5,
                                 missing_y,
                                 ts_y['precip_mm'], ts_y['temp_degC'], ts_y['discharge_mm'],
                                 ts_m['precip_mm'], ts_m['temp_degC'], ts_m['discharge_mm'],
                                 fdc_precip.values**0.5, fdc_dis.values**0.5,
                                 ]},
                             {
                                 "yaxis.type": "linear", "yaxis.title.text": "sqrt mm",
                                 "yaxis8.type": "linear", "yaxis8.title.text": "sqrt mm",
                             }
                         ])
                ],
            )
        ],
    )
    fig.add_annotation(
        text=signature_text, 
        xref="paper", x=1.02, xanchor="left", 
        yref="paper", y=1, yanchor="top",
        showarrow=False, align="left", bgcolor="rgba(255, 255, 255, 0.9)"
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
    fig.update_layout(height=None, width=None, autosize=True)

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
                    setTimeout(function() {{ window.dispatchEvent(new Event('resize')); }}, 200); 
                }});
            </script>
        </body>
        </html>
        """
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(full_page_html)