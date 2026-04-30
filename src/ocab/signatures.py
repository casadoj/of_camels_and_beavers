import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import logging

logger = logging.getLogger(__name__)


def annual_runoff(discharge: pd.Series, area: float) -> float:
    """Average annual runoff (in mm).

    Parameters:
    -----------
    discharge: pd.Series
        Time series of discharge (m³/s). Index are dates and values are discharge
    area: float
        Catchment area (km²)

    Returns:
    --------
    float
        Annual runoff (mm)
    """

    # average specific discharge (m/s)
    avg_q = discharge.mean(skipna=True) / (area * 1e6)
    # convert to mm
    avg_q *= 1000 * 3600 * 24 * 365
    return  avg_q 


def flashiness_index(discharge: pd.Series) -> float:
    """Richards-Baker Flashiness Index (RBI)
    
    Parameters:
    -----------
    discharge: pd.Series
        Time series of discharge. Index are dates and values are discharge

    Returns:
    --------
    float
        Flashiness index
    """

    diff = discharge.diff().abs()
    volume = discharge.loc[diff.notnull()].sum()

    return diff.sum() / volume if volume > 0 else np.nan


def flow_duration_curve(discharge: pd.Series) -> pd.Series:
    """Creates the flow duration curve

    Parameters:
    -----------
    discharge: pd.Series
        Time series of discharge. Index are dates and values are discharge
    
    Returns:
    --------
    pd.Series
        Flow duration curve. Index is the probability of exceedance and values are the asscociated discharge
    """
    # sorted discharge
    Q = discharge.copy()
    Q = Q.dropna().sort_values(ascending=False).values
    
    # probability of exceedance
    n = len(Q) + 1
    probs = np.arange(1, n) / n

    fdc = pd.Series(data=Q, index=probs, name='discharge')
    fdc.index.name = 'probability'

    return fdc


def slope_fdc(discharge: pd.Series, quantiles=[.333, .666]) -> [pd.Series, float]:
    """Computes the slope of the flow duration curve between the two specified quantiles
    
    Parameters:
    -----------
    discharge: pd.Series
        Time series of discharge. Index are dates and values are discharge
    quantiles: list of floats
        Values of probability of exceedance use to compute the slope

    Returns:
    --------
    fdc: pd.Series
        Flow duration curve. Index is the probability of exceedance and values are the asscociated discharge
    slope: float
        Slope of the flow duration curve between the two quantiles
    """
    if len(quantiles) != 2:
        raise ValueError(f"'quantiles must be a list of two values: {quantiles}")
    
    if discharge.isnull().all():
        logger.info('Empty time series')
        return pd.Series(index=np.linspace(0, 1, num=11)), np.nan
    
    # compute the flow duration curve
    fdc = flow_duration_curve(discharge)
    function = interp1d(fdc.index, fdc.values)
    
    # compute discharge quantiles
    discharges = np.array([function(q) for q in quantiles])

    # compute slope of the flow duration curve
    slope = np.abs(np.diff(np.log10(discharges + 1e-6))).item() / np.abs(np.diff(quantiles)).item()

    return fdc, slope


def baseflow_index(discharge: pd.Series, alpha: float = 0.925) -> float:
    """
    Computes the Baseflow Index (BFI) using the Lyne-Hollick digital filter.
    
    Parameters:
    -----------
    discharge: pd.Series
        Daily discharge values.
    alpha: float
        Filter parameter (default 0.925).
        
    Returns:
    --------
    pd.DataFrame: time series of total and base flow
    float: Baseflow Index (0 to 1)
    """

    # Extract total flow
    total = discharge.values
    n = len(total)     
    
    # Compute quick flow
    quick = np.zeros(n)
    factor = (1 + alpha) / 2
    for t in range(1, n):
        # Calculate quickflow
        q_val = alpha * quick[t-1] + factor * (total[t] - total[t-1])
        q_val = 0 if np.isnan(q_val) else q_val

        # Apply constraints: 0 <= quickflow <= total_flow
        if q_val < 0:
            q_val = 0
        elif q_val > total[t]:
            q_val = total[t]
        
        quick[t] = q_val
            
    # Concatenate series
    series = pd.DataFrame({
        'total': pd.Series(total, index=discharge.index),
        'base': pd.Series(total - quick, index=discharge.index)
    })

    # Calculate BFI    # Compute BFI
    cumulative = series.dropna(axis=0, how='any').sum()
    bfi = cumulative.base / cumulative.total if cumulative.total > 0 else np.nan
    
    return series, float(bfi)


def budyko(aridity: float, n: float = 2):
    """Computes the expected evaporative index in the Budyko framework:
    
    Parameters:
    -----------
    aridity: float
        Aridity index: quotient of the potential evapotranspiration and precipitation
    n: float
        Exponent in the Budyko formulation

    Returns:
    --------
    evaporativity: float
        Evaporative index: quotient of the actual evapotranspiration and precipitation
    """
    return (1 + aridity**-n)**(-1/n)