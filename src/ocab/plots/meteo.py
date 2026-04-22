import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _compute_monthly_climatology(meteo: pd.DataFrame) -> pd.DataFrame:
    """Creates a monthly climatology by resampling the daily data and then averaging across months."""
    meteo_monthly = meteo.resample('MS').agg({
        'temp_degC': 'mean',
        'precip_mm': 'sum',
        'pet_mm': 'sum'
    })
    return meteo_monthly.groupby(meteo_monthly.index.month).mean()

def _compute_annual_timeseries(meteo: pd.DataFrame) -> pd.DataFrame:
    """Creates the annual time series by resampling the daily data."""
    return meteo.resample('YS').agg({
        'temp_degC': 'mean',
        'precip_mm': 'sum',
        'pet_mm': 'sum'
    })

def plot_meteo_timeseries(
        meteo: pd.DataFrame, 
        save: bool = False,
        **kwargs
    ) -> go.Figure:
    """
    Creates an interactive figure with three plots: the daily and annual time series, and 
    the climograph.
    
    Parameters:
    -----------
    meteo: pandas.Series
        Meteorological time series with daily resolution. Must contain the following columns:
        - temp_degC: Temperature in degrees Celsius
        - precip_mm: Precipitation in millimeters
    save: boolean
        If True, return an object with the Plotly figure. If false, show the figure
    
    Keyword arguments:
    ------------------
    c_precip: string
        Color used to plot precipitation
    c_temp: string
        Color used to plot temperature
    title: string
        Figure title
    """
    
    c_precip = kwargs.get('c_precip', 'lightblue')
    c_temp = kwargs.get('c_temp', 'darkred')
    title = kwargs.get('title', None)

    # 1. Setup Grid
    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.75, 0.25],
        row_heights=[0.8, 0.2],
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
            [{"secondary_y": True}, None]],
        subplot_titles=("Daily Time Series", "Climograph", "Annual Time Series"),
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
        shared_xaxes=False
    )

    # --- PLOT 1: DAILY TIME SERIES ---

    # add traces
    fig.add_trace(go.Bar(
            x=meteo.index, 
            y=meteo['precip_mm'], 
            name="Precipitation", 
            marker_color=c_precip, 
            marker_line_width=0,
            legendgroup="Precipitation",
            showlegend=True
        ), row=1, col=1
    )
    fig.add_trace(go.Scatter(
            x=meteo.index, 
            y=meteo['temp_degC'], 
            name="Temperature", 
            line=dict(color=c_temp, width=0.5),
            legendgroup="Temperature",
            showlegend=True
        ), row=1, col=1, secondary_y=True
    )

    # define Y axis limits
    factor = 4
    round_p = 20
    round_t = round_p / factor
    # get rounded max/min temperature and precipitation values
    daily_p_min = 0.0
    daily_p_max = np.ceil(meteo['precip_mm'].max() / round_p) * round_p
    daily_t_min = np.floor(meteo['temp_degC'].min() / round_t) * round_t
    daily_t_max = np.ceil(meteo['temp_degC'].max() / round_t) * round_t
    # get rounded max/min temperature and precipitation values
    daily_p_max = max(daily_p_max, daily_t_max * factor) + 1
    daily_p_min = min(daily_p_min, daily_t_min * factor) - 1
    daily_t_max, daily_t_min = daily_p_max / factor, daily_p_min / factor

    # set axes properties
    fig.update_yaxes(
        title_text="mm", 
        range=[daily_p_min, daily_p_max], 
        dtick=round_p, 
        row=1, col=1, secondary_y=False
    )
    fig.update_yaxes(
        title_text="°C", 
        range=[daily_t_min, daily_t_max], 
        dtick=round_t, 
        row=1, col=1, secondary_y=True
    )
    fig.add_hline(
        y=0, 
        line_width=0.8, 
        line_color="black", 
        layer="above",
        row=1, col=1
    )

    # --- PLOT 2: CLIMOGRAPH---

    # compute monthly climatology
    meteo_m = _compute_monthly_climatology(meteo)

    # add traces
    fig.add_trace(go.Bar(
            x=meteo_m.index, 
            y=meteo_m['precip_mm'], 
            name="Precipitation", 
            marker_color=c_precip, 
            opacity=0.8,
            legendgroup="Precipitation",
            showlegend=False
        ), row=1, col=2
    )
    fig.add_trace(go.Scatter(
            x=meteo_m.index, 
            y=meteo_m['temp_degC'], 
            name="Temperature", 
            line=dict(color=c_temp, width=2),
            legendgroup="Temperature",
            showlegend=False
        ), row=1, col=2, secondary_y=True
    )

    # define Y axis limits
    factor = .5
    round_p = 20
    round_t = round_p * factor
    month_p_max = np.ceil(meteo_m['precip_mm'].max() / round_p) * round_p + 2
    month_t_max = factor * month_p_max

    # set axes properties
    fig.update_yaxes(
        title_text="mm", 
        range=[0, month_p_max], 
        dtick=round_p, 
        row=1, col=2, secondary_y=False
    )
    fig.update_yaxes(
        title_text="°C", 
        range=[0, month_t_max], 
        dtick=round_t, 
        row=1, col=2, secondary_y=True
    )
    fig.update_xaxes(
        tickvals=list(range(1, 13)), 
        ticktext=['J','F','M','A','M','J','J','A','S','O','N','D'], 
        row=1, col=2
    )

    # --- PLOT 3: ANNUAL MEANS ---

    # compute annual time series
    meteo_y = _compute_annual_timeseries(meteo)
    
    # add traces
    fig.add_trace(go.Bar(
            x=meteo_y.index, 
            y=meteo_y['precip_mm'], 
            name="Precipitation", 
            marker_color=c_precip, 
            opacity=0.8,
            legendgroup="Precipitation",
            showlegend=False
        ), row=2, col=1
    )
    fig.add_trace(go.Scatter(
            x=meteo_y.index, 
            y=meteo_y['temp_degC'], 
            name="Temperature",
            line=dict(color=c_temp, width=2),
            legendgroup="Temperature",
            showlegend=False
        ), row=2, col=1, secondary_y=True
    )

    # Link X-Axis of Row 1, Col 1 and Row 2, Col 1
    fig.update_layout(xaxis3=dict(matches='x'))
    
    # define Y axis limits
    factor = 100
    year_p_max = 3050
    dtick_p = 500
    year_t_max = year_p_max / factor
    dtick_t = dtick_p / factor

    # set axes properties
    fig.update_yaxes(
        title_text="mm", 
        range=[0, year_p_max], 
        dtick=dtick_p, 
        row=2, col=1, secondary_y=False
    )
    fig.update_yaxes(
        title_text="°C", 
        range=[0, year_t_max], 
        dtick=dtick_t, 
        row=2, col=1, secondary_y=True
    )

    # Update layout
    fig.update_layout(
        title_text=f"<b>{title if title else ''}</b>",
        title_x=0.5,
        height=800, 
        template="plotly_white", 
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            xanchor="center",
            y=0.1,
            x=0.87,
            bgcolor="rgba(0, 0, 0, 0)", # Semi-transparent background
            borderwidth=0
        ),
        bargap=0.075, 
        barmode='overlay'
    )

    if save:
        return fig
    else:
        fig.show()
