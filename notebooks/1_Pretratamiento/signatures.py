import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


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

    return diff.sum() / volume


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
    sorted_q = discharge.sort_values(ascending=False).values
    
    # probability of exceedance
    n = len(sorted_q) + 1
    probs = np.arange(1, n) / n

    fdc = pd.Series(data=sorted_q, index=probs, name='discharge')
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
        
        # Apply constraints: 0 <= quickflow <= total_flow
        if q_val < 0:
            q_val = 0
        elif q_val > total[t]:
            q_val = total[t]
            
        quick[t] = q_val
        
    base = total - quick
    
    # Calculate BFI
    total_sum = np.sum(total)
    bfi = np.sum(base) / total_sum if total_sum > 0 else 0.0
    
    return float(bfi)