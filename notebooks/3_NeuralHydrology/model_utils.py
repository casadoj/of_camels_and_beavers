import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle
from typing import Dict, List, Union


def plot_results(results: Dict, period: str, target: str, save: Union[str, Path] = None, **kwargs):
    """
    """
    
    figsize = kwargs.get('figsize', (16, 4))
    ylim = kwargs.get('ylim', (-1, None))
    
    for id, dct in results.items():

        fig, ax = plt.subplots(figsize=figsize)#, sharex=True, sharey=True)

        # extraer series
        qobs = dct['1D']['xr'][f'{target}_obs'].isel(time_step=0).to_pandas()
        qsim = dct['1D']['xr'][f'{target}_sim'].isel(time_step=0).to_pandas()
        
        # plot series
        qobs.plot(c='darkgray', lw=1, label='obs', ax=ax)
        qsim.plot(c='steelblue', lw=1.2, label='sim', ax=ax)

        # config
        ax.set(xlabel='', ylabel=(f'{target} (mm/d)'), ylim=ylim)
        ax.set_title(f'{id} - {period}')
        ax.text(0.01, 0.925, 'KGE = {0:.3f}'.format(dct['1D']['KGE']), transform=ax.transAxes, fontsize=11)
        ax.legend(loc=0, frameon=False);

        if save is not None:
            plt.savefig(f'{save}/{id:04}.jpg', dpi=300, bbox_inches='tight')
        
        
        
def get_results(run_dir: Path, period: str, epoch: int) -> (dict, pd.DataFrame):
    """Extrae 
    """
    
    path = run_dir / period / f'model_epoch{epoch:03}'
    
    # time series
    # with open(path / f'{period}_results.p', 'rb') as fp:
    #     results = pickle.load(fp)
    results = pd.read_pickle(path / f'{period}_results.p')
        
    # metrics
    metrics = pd.read_csv(path / f'{period}_metrics.csv', index_col='basin')
    
    return results, metrics