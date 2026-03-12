import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional

from signatures import annual_runoff, baseflow_index, flashiness_index, slope_fdc

def plot_timeseries_interactive(
    ts: pd.Series, 
    area: float,
    regime: Optional[str] = None,
    save: Optional[str] = None, 
    **kwargs
    ):

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
    fig = make_subplots(
        rows=1, cols=2, 
        shared_yaxes=True, 
        column_widths=[0.7, 0.25], 
        horizontal_spacing=0.03,
        subplot_titles=("Hydrograph", "Flow Duration Curve")
    )

    # 3. Add traces
    fig.add_trace(go.Scatter(x=ts.index, y=ts.values, line=dict(color=c, width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=fdc.index * 100, y=fdc.values, line=dict(color=c, width=2)), row=1, col=2)    

    # 4. Update Layout
    fig.update_layout(
        title_text=f"<b>{title if title else ''}</b>", # Global figure title
        title_x=0.5,                                   # Center the title
        margin=dict(l=50, r=250, t=100, b=50),         # LARGE right margin (250px)
        template="plotly_white",
        height=550,
        showlegend=False,
        annotations=[
            dict(
                text=signature_text,
                xref="paper", yref="paper",
                x=1.02,            # Starts at 105% of the plot width
                xanchor="left",    # Anchor box to its own left edge
                y=1,             # Center vertically
                yanchor="top",
                showarrow=False,
                align="left",
                font=dict(size=12),
                bgcolor="rgba(255, 255, 255, 0.9)", # Semi-transparent white
                # bordercolor="black",
                # borderwidth=1
            )
        ],
        updatemenus=[
            dict(
                type="buttons",
                direction="down",
                active=0,
                x=0.0, 
                y=1.25,
                buttons=[
                    dict(label="Linear Scale", method="relayout", 
                         args=[{"yaxis.type": "linear", "yaxis2.type": "linear"}]),
                    dict(label="Log Scale", method="relayout", 
                         args=[{"yaxis.type": "log", "yaxis2.type": "log"}]),
                ],
            )
        ]
    )

    # Update Axes Titles
    fig.update_yaxes(title_text="Discharge (m³/s)", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Exceedance Prob. (%)", row=1, col=2)

    if save:
        fig.write_html(str(save))
    else:
        fig.show()