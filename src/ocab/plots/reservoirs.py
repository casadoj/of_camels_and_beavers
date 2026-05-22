from pathlib import Path
# from typing import Optional
import logging

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio


from ocab.plots.utils import compute_annual_timeseries, compute_monthly_climatology, compute_climatology, define_y_limits
from ocab.signatures import baseflow_index, flashiness_index, slope_fdc, budyko

logger = logging.getLogger(__name__)


def plot_reservoir_timeseries(
    ts: pd.DataFrame,
    attributes: pd.Series,
    save: bool = False,
    **kwargs
    ):
    """
    Creates an interactive figure with two plots: the time series and the Budyko diagram.
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
    alpha: float
        Transparency of the precipitation bar plot
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
    alpha = kwargs.get('alpha', 0.2)
    c_fill = kwargs.get('c_fill', 'darkslategrey')
    c_in = kwargs.get('c_line', 'seagreen')
    c_out = kwargs.get('c_line', 'darkred')
    c_precip = kwargs.get('c_bar', 'lightblue')
    title = kwargs.get('title', None)

    # extract time series
    variables = ['filling', 'inflow_cms', 'inflow_mm', 'outflow_cms', 'outflow_mm', 'precip_mm', 'temp_degC', 'pet_mm']
    missing_vars = list(set(variables).difference(ts.columns))
    if len(missing_vars) > 0:
        ts[missing_vars] = np.nan

    # Setup grid
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
        subplot_titles=("Daily Time Series", "", "Annual Time Series", 'Climatology', "Budyko Diagram"),
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
            showlegend=False
        ),
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts.index, 
            y=ts['inflow_mm'], 
            name="Inflow", 
            line=dict(color=c_in, width=1), 
            legendgroup="Inflow",
            showlegend=False
        ),
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts.index, 
            y=ts['outflow_mm'], 
            name="Outflow", 
            line=dict(color=c_out, width=1), 
            legendgroup="Outflow", 
            showlegend=False
        ),
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts.index, 
            y=ts['filling'], 
            name="Filling", 
            line=dict(color=c_fill, width=1), 
            legendgroup="Filling", 
            showlegend=False
        ), 
        row=row, col=col, secondary_y=True
    )

    # set axes properties
    round_mm_d = 20
    scale_d = 100
    mm_range_d, fill_range_d = define_y_limits(
        ts, 
        round_mm_d, 
        scale_d,
        cols_primary=['precip_mm', 'inflow_mm', 'outflow_mm'],
        cols_secondary=['filling']
    )
    fig.update_yaxes(
        title_text="mm", 
        # rangemode='nonnegative',
        range=mm_range_d,
        dtick=round_mm_d,
        row=row, col=col, secondary_y=False
    )
    fig.update_yaxes(
        title_text="Filling (-)",
        range=fill_range_d,
        dtick=round_mm_d / scale_d,
        row=row, col=col, secondary_y=True,
    )

    # --- PLOT 2: MISSING DATA ---

    row, col = 2, 1
    size = 2.5

    # find missing outflow dates
    missing_x_in = ts[ts['inflow_mm'].isnull()].index
    missing_y_in = [0] * len(missing_x_in)
    fig.add_trace(
        go.Scatter(
            x=missing_x_in,
            y=missing_y_in, 
            mode='markers',
            marker=dict(
                symbol='line-ns-open',
                size=size,
                color=c_in,
                line_width=1
            ),
            legendgroup="Inflow",
            showlegend=False,
            hoverinfo='x'
        ),
        row=row, col=col
    )
    # find missing outflow dates
    missing_x_out = ts[ts['outflow_mm'].isnull()].index
    missing_y_out = [10] * len(missing_x_out)
    fig.add_trace(
        go.Scatter(
            x=missing_x_out,
            y=missing_y_out, 
            mode='markers',
            marker=dict(
                symbol='line-ns-open',
                size=size,
                color=c_out,
                line_width=1
            ),
            legendgroup="Outflow",
            showlegend=False,
            hoverinfo='x'
        ),
        row=row, col=col
    )
    # find missing filling dates
    missing_x_fill = ts[ts['filling'].isnull()].index
    missing_y_fill = [20] * len(missing_x_fill)
    fig.add_trace(
        go.Scatter(
            x=missing_x_fill,
            y=missing_y_fill, 
            mode='markers',
            marker=dict(
                symbol='line-ns-open',
                size=size,
                color=c_fill,
                line_width=1
            ),
            legendgroup="Filling",
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
    ts_y = compute_annual_timeseries(ts)
    ts_y.index += pd.DateOffset(months=6) # to adapt labels in the plots

    # add traces
    fig.add_trace(
        go.Bar(
            x=ts_y.index, 
            y=ts_y['precip_mm'], 
            name="Precipitation", 
            marker_color=c_precip, 
            opacity=1 - alpha,
            legendgroup="Precipitation",
            showlegend=True,
            hovertemplate="<b>Year: %{x|%Y}</b><br>P: %{y:.0f} mm<extra></extra>"
        ),
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts_y.index, 
            y=ts_y['inflow_mm'], 
            name="Inflow",
            line=dict(color=c_in, width=2),
            legendgroup="Inflow",
            showlegend=True,
            hovertemplate="<b>Year: %{x|%Y}</b><br>I: %{y:.0f} mm<extra></extra>"
        ),
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts_y.index, 
            y=ts_y['outflow_mm'], 
            name="Outflow",
            line=dict(color=c_out, width=2),
            legendgroup="Outflow",
            showlegend=True,
            hovertemplate="<b>Year: %{x|%Y}</b><br>O: %{y:.0f} mm<extra></extra>"
        ),
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts_y.index, 
            y=ts_y['filling'], 
            name="Filling",
            line=dict(color=c_fill, width=2),
            legendgroup="Filling",
            showlegend=True,
            hovertemplate="<b>Year: %{x|%Y}</b><br>F: %{y:.2f}<extra></extra>"
        ),
        row=row, col=col, secondary_y=True
    )

    # set axes properties
    round_mm_y = 500
    scale_y = 1000
    mm_range_y, fill_range_y = define_y_limits(
        ts_y, 
        round_mm_y, 
        scale_y,
        cols_primary=['precip_mm', 'inflow_mm', 'outflow_mm'],
        cols_secondary=['filling']
    )
    fig.update_yaxes(
        title_text="mm", 
        range=mm_range_y, 
        dtick=round_mm_y, 
        row=row, col=col
    )
    fig.update_yaxes(
        title_text="Filling (-)",
        range=fill_range_y,
        dtick=round_mm_y / scale_y,
        row=row, col=col, secondary_y=True,
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
            legendgroup="Precipitation",
            showlegend=False
        ), 
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts_m.index, 
            y=ts_m['inflow_mm'], 
            name="Inflow", 
            line=dict(color=c_in, width=2),
            legendgroup="Inflow",
            showlegend=False
        ), 
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts_m.index, 
            y=ts_m['outflow_mm'], 
            name="Outflow", 
            line=dict(color=c_out, width=2),
            legendgroup="Outflow",
            showlegend=False
        ), 
        row=row, col=col
    )
    fig.add_trace(
        go.Scatter(
            x=ts_m.index, 
            y=ts_m['filling'], 
            name="Filling", 
            line=dict(color=c_fill, width=2),
            legendgroup="Filling",
            showlegend=False
        ),
        row=row, col=col, secondary_y=True
    )

    # set axes properties
    round_mm_m = 20
    scale_m = 100
    mm_range_m, fill_range_m = define_y_limits(
        ts_m, 
        round_mm_m,
        scale_m,
        cols_primary=['precip_mm', 'inflow_mm', 'outflow_mm'],
        cols_secondary=['filling']
    )
    fig.update_yaxes(
        title_text="mm", 
        range=mm_range_m, 
        dtick=round_mm_m, 
        row=row, col=col
    )
    fig.update_yaxes(
        title_text="Filling (-)",
        range=fill_range_m,
        dtick=round_mm_m / scale_m,
        row=row, col=col, secondary_y=True,
    )
    fig.update_xaxes(
        tickvals=list(range(1, 13)), 
        ticktext=['J','F','M','A','M','J','J','A','S','O','N','D'], 
        row=row, col=col
    )

    # --- PLOT 5: BUDYKO DIAGRAM ---

    row, col = 4, 2

    # calculate indices
    aridity = ts_y['pet_mm'] / ts_y['precip_mm']
    evaporativity = (ts_y['precip_mm'] - ts_y['outflow_mm']) / ts_y['precip_mm']

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
            customdata=aridity.index.year,
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

    # compute flow duration curve
    _, slope_outflow = slope_fdc(ts['outflow_mm'])

    # --- SIGNATRUES & CLIMATOLOGY ---

    # 1. Compute hydrological signatures
    _, bfi_outflow = baseflow_index(ts['outflow_cms'])
    fi_outflow = flashiness_index(ts['outflow_cms'])

    # Calculate Climatology
    climatology = compute_climatology(ts)

    signature_text = (
        "<b>Properties</b><br>"
        f"Capacity: {attributes.cap_mcm:.1f} hm³<br>"
        f"Surface: {attributes.area_skm:.1f} km²<br>"
        f"Catchment: {attributes.catch_skm:.1f} km²<br>"
        f"Deg. Regulation: {attributes.dor_d:.0f} days<br>"
        f"Deg. Disruptivity: {attributes.dod_m * 1000:.0f} mm<br>"
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

    # Update Layout & Scale Buttons
    y_raw = [ts['precip_mm'], ts['inflow_mm'], ts['outflow_mm']]
    y_sqrt = [trace**.5 for trace in y_raw]
    fig.update_layout(
        title_text=f"<b>{title if title else ''}</b>",
        title_x=0.01,
        title_xanchor='left',
        title_y=0.99,
        title_yanchor='top',
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
                type="buttons", direction="down", active=0, x=1.02, xanchor="left", y=1, yanchor='top', showactive=True,
                buttons=[
                    dict(label="Linear Scale", method="update", 
                         args=[
                             {"y": y_raw},
                             {"yaxis.type": "linear", "yaxis.title.text": "mm" },
                             [0, 1, 2]
                         ]),
                    dict(label="Sqrt Scale", method="update",
                         args=[
                             {"y": y_sqrt},
                             {"yaxis.type": "linear", "yaxis.title.text": "sqrt mm"},
                             [0, 1, 2]
                         ]),
                    dict(label="Log Scale", method="update",
                         args=[
                             {"y": y_raw}, 
                             {"yaxis.type": "log", "yaxis.title.text": "log mm"},
                             [0, 1, 2]
                         ]),
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


def create_reservoir_html(
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

    # # Convert figure to HTML div string
    # plotly_html = fig.to_html(
    #     full_html=False, 
    #     include_plotlyjs='cdn',
    #     config={'responsive': True}
    # )

    # Convert figure to HTML div string
    plotly_html = pio.to_html(
        fig, 
        full_html=False, 
        include_plotlyjs='cdn',
        include_mathjax=False,
        config={'responsive': True, 'displaylogo': False}
    )

    title = Path(path).stem

    full_page_html = f"""
        <html>
        <head>
            <meta charset="utf-8" />
            <title>{title}</title>
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
                    const baseUrl = "https://docs.google.com/forms/d/e/1FAIpQLSdcqEbw2bhJXLUqHFCQLBz0LEbCBUesnxeT32L5l5XkNAfMyg/viewform?embedded=true";
                    const emailEntryId = "204970380";
                    const stationEntryId = "889543648";
                    const startEntry1Id = "1625252996";
                    const endEntry1Id = "314932285";
                    const startEntry2Id = "1590382732";
                    const endEntry2Id = "1770881539";

                    const userEmail = localStorage.getItem('userEmail') || "";
                    const filename = window.location.pathname.split('/').pop();
                    const stationId = filename.replace('.html', '');
                    const start = "{start}";
                    const end = "{end}";

                    const finalUrl = baseUrl + 
                        "&entry." + stationEntryId + "=" + stationId + 
                        "&entry." + emailEntryId + "=" + encodeURIComponent(userEmail) + 
                        "&entry." + startEntry1Id + "=" + start + 
                        "&entry." + endEntry1Id + "=" + end
                        "&entry." + startEntry2Id + "=" + start + 
                        "&entry." + endEntry2Id + "=" + end;

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