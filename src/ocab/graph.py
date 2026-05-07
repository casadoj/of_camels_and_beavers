from typing import Hashable, Iterable, Literal, Optional, Union
from pathlib import Path
import pyproj
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from rasterio import features

import pyflwdir


def load_MERIT_points(
        path: Union[str, Path],
        flwdir: pyflwdir.FlwdirRaster,
        crs: Union[str, int, pyproj.CRS] = 4326, 
        kind: Literal['station', 'dam', 'outlet'] = 'station',
    ) -> gpd.GeoDataFrame:
    """
    Load a GeoJSON/Shapefile of points located in the MERIT DEM grid.
    
    This function is designed to process the output of the `basin-delineation` tool,
    ensuring correct column naming, kind assignment, and CRS alignment.

    Parameters:
    -----------
    path : str or pathlib.Path
        The path to the vector file (GeoJSON, SHP, etc.) containing the points.
    crs : str, int, or pyproj.CRS
        The target Coordinate Reference System (e.g., "EPSG:4326", 4326, or a 
        pyproj.CRS object) to which the data should be reprojected.
    kind : {'station', 'dam', 'outlet'}, default 'station'
        A label to categorize the points in the 'kind' column of the GeoDataFrame.

    Returns:
    --------
    gdf : geopandas.GeoDataFrame
        A GeoDataFrame indexed by 'id' containing the geometry, drainage area 
        (area_skm), and point category.
    """

    # load file
    gdf = gpd.read_file(path, columns=['id', 'geometry', 'area_3sec'])

    # standardize columns
    gdf.rename(columns={'area_3sec': 'area_skm'}, inplace=True)
    gdf['kind'] = kind
    gdf.set_index(['id', 'kind'], inplace=True)

    # reproject, if necessary
    if gdf.crs != crs:
        gdf.to_crs(crs)

    # remove spatial duplicates
    gdf.drop_duplicates(subset='geometry', inplace=True)

    # get pixel indices in the flow direction object
    gdf['pixel'] = flwdir.index(
        xs=gdf.geometry.x,
        ys=gdf.geometry.y
    )
    
    return gdf


def vectorize(data, nodata, transform, crs, name="value"):
    feats_gen = features.shapes(
        data,
        mask=data != nodata,
        transform=transform,
        connectivity=8,
    )
    feats = [
        {"geometry": geom, "properties": {name: val}} for geom, val in list(feats_gen)
    ]

    # parse to geopandas for plotting / writing to file
    gdf = gpd.GeoDataFrame.from_features(feats, crs=crs)
    gdf[name] = gdf[name].astype(data.dtype)
    return gdf


def delineate_subbasins(
        points: gpd.GeoDataFrame,
        flwdir: pyflwdir.FlwdirRaster,
        uparea: np.ndarray,
        name: str = 'subbasin'
    ) -> gpd.GeoDataFrame:
    """
    Delineate subbasins for a set of points using a flow direction raster.

    This function maps GeoPandas points to their corresponding pixel indices in a 
    pyflwdir stream network, delineates the contributing area (subbasin) for each, 
    and vectorizes the resulting raster masks into a GeoDataFrame.

    Parameters:
    -----------
    points : gpd.GeoDataFrame
        A GeoDataFrame containing the outlet points. Must have a valid CRS and 
        an index that serves as the unique identifier for each point.
    flwdir : pyflwdir.FlwdirRaster
        The flow direction object initialized from a DEM or flow direction grid, 
        containing the spatial transform and topology.
    uparea : np.ndarray
        A 2D NumPy array representing the upstream drainage area (typically in km²) 
        matching the extent and resolution of the flwdir object.
    name : str, default 'subbasin'
        The name assigned to the initial integer-labeled column in the 
        vectorized GeoDataFrame before it is mapped to point IDs.

    Returns:
    --------
    subbasins : gpd.GeoDataFrame
        A GeoDataFrame of subbasin polygons indexed by the original point IDs. 
        Includes the following columns:
            - 'geometry': The polygon boundary of the subbasin.
            - 'area_skm': The upstream drainage area value at the outlet pixel.
    """

    if 'pixel' not in points.columns:
        # get pixel indices in the flow direction object
        points['pixel'] = flwdir.index(
            xs=points.geometry.x,
            ys=points.geometry.y
        )

    # delineate the station subbasins
    subbasins_map = flwdir.basins(idxs=points['pixel'])

    # convert to GeoDataFrame
    subbasins = vectorize(
        data=subbasins_map.astype(np.int32), 
        nodata=0, 
        transform=flwdir.transform, 
        crs=points.crs, 
        name=name
    )

    # Assign point ID
    subbasin_to_point = pd.Series(
        list(points.index), 
        index=subbasins_map.ravel()[points.pixel]
        ).to_dict()
    # subbasins[['id', 'kind']] = subbasins[name].map(subbasin_to_point)
    subbasins[['id', 'kind']] = subbasins[name].map(subbasin_to_point).apply(pd.Series)
    subbasins.set_index(['id', 'kind'], drop=True, inplace=True)

    # Extract upstream area
    subbasins['area_skm'] = uparea.ravel()[points.loc[subbasins.index, 'pixel']]#.round(0).astype(int)

    # if save:
    #     subbasins.to_file(save, driver='GeoJSON')

    return subbasins


def find_downstream_neighbour(
        idx: int, 
        flwdir: pyflwdir.FlwdirRaster, 
        lookup_dict: dict
    ) -> int:
    """
    Finds the station inmediately downstream of the input point.

    Parameters:
    -----------
    idx: int
        Identifier of the input pixel in the flow direction raster (`flwdir`)
    flwdir: pyflwdir.FlwdirRaster
        Flow direction raster
    lookup_dict: dictionary
        Keys are pixel IDs in `flwdir` and values the station IDs

    Returns:
    --------
    int: the ID of the station inmediately downstream
    float: distance to the outlet in meters
    """

    # draw the flowpath
    paths, dists = flwdir.path(idx, unit='m')
    path, dist = paths[0], dists[0]

    # find station in that flowpath
    for pixel in path[1:]:
        if pixel in lookup_dict:
            ID = lookup_dict[pixel]
            return (ID, dist)
    
    return (pd.NA, dist)


def sort_points_geographically(
        points: gpd.GeoDataFrame, 
        center_x: float = -3.7, 
        center_y: float = 40.0,
        inplace: bool = False
    ) -> gpd.GeoDataFrame:
    """
    Sorts point geometries counter-clockwise based on their angle from a central coordinate.

    The sorting starts from the North-East (roughly the French-Cantabrian border) 
    by applying a 60-degree offset to the calculated polar coordinates.

    Parameters:
    -----------
    points : gpd.GeoDataFrame
        The GeoDataFrame containing point geometries to be sorted.
    center_x : float, default -3.7
        The longitude (X coordinate) of the reference center point for 
        calculating angles.
    center_y : float, default 40.0
        The latitude (Y coordinate) of the reference center point for 
        calculating angles.
    inplace : bool, default False
        If True, the input GeoDataFrame is modified. If False, a sorted 
        copy is returned.

    Returns:
    --------
    gpd.GeoDataFrame
        The sorted GeoDataFrame. If `inplace=True`, returns the original 
        object updated; otherwise returns a new object.
    """

    gdf = points.copy()

    # sort outlets counter-clockwisely starting from the North
    gdf['angle'] = np.arctan2(
        gdf.geometry.y - center_y, 
        gdf.geometry.x - center_x
        )
    gdf['angle'] = (gdf['angle'] - np.radians(60)) % (2 * np.pi) # start in the French Cantabrian border
    gdf.sort_values('angle', inplace=True)
    gdf.drop(['angle'], axis=1, inplace=True)

    if inplace:
        points = gdf
    else:
        return points
    

def find_outlets(
        points: gpd.GeoDataFrame,
        flwdir: pyflwdir.FlwdirRaster,
        uparea: np.ndarray,
        sort: bool = True,
    ) -> gpd.GeoDataFrame:
    """
    Identifies unique river outlets by tracing flow paths from input points.

    Parameters:
    -----------
    points : gpd.GeoDataFrame
        Input locations (e.g., stations or dams). Must contain point geometries.
        If a 'pixel' column is missing, it will be calculated using the flwdir.
    flwdir : pyflwdir.FlwdirRaster
        Flow direction raster object used to trace the downstream paths.
    uparea : np.ndarray
        A 2D array (flattened during processing) representing the upstream 
        contributing area for each pixel in the raster.
    sort : bool, default True
        If True, sorts the resulting outlets geographically using the 
        `sort_points_geographically` helper function.

    Returns:
    --------
    gpd.GeoDataFrame
        A GeoDataFrame of the unique outlet points. Includes:
        - pixel: The raster index of the outlet.
        - area_skm: Upstream area at the outlet pixel.
        - geometry: Point geometry in the same CRS as the input.
        - MultiIndex: Indexed by ['id', 'kind'], where kind is 'outlet'.
    """

    if 'pixel' not in points.columns:
        # get pixel indices in the flow direction object
        points['pixel'] = flwdir.index(
            xs=points.geometry.x,
            ys=points.geometry.y
        )
    
    # compute all flowpaths from the points
    paths, dists = flwdir.path(points.pixel, unit='m')

    # find unique river outlets
    outlets_idx = list(set(path[-1] for path in paths))

    # create GeoDataFrame of outlets
    outlets = gpd.GeoDataFrame(
        {
            'pixel': outlets_idx,
            'area_skm': uparea.ravel()[outlets_idx]
        },
        geometry=gpd.points_from_xy(*flwdir.xy(idxs=outlets_idx)),
        crs=points.crs
    )

    if sort:
        # sort outlets geographically
        sort_points_geographically(outlets, inplace=True)

    # create MultiIndex
    outlets['id'] = range(1, len(outlets) + 1)
    outlets['kind'] = 'outlet'
    outlets.set_index(['id', 'kind'], inplace=True)

    return outlets


def plot_graph(
        graph: nx.DiGraph, 
        nodes: Iterable[Hashable], 
        labels: bool = False, 
        streams: Optional[gpd.GeoDataFrame] = None,
        basins: Optional[gpd.GeoDataFrame] = None,
        subbasins: Optional[gpd.GeoDataFrame] = None,
        **kwargs
    ) -> None:
    """
    Plots a specific set of nodes from a NetworkX graph onto a geographic map.

    This function creates a subgraph based on the provided nodes, extracts 
    geographic coordinates (lon/lat) from node attributes, and overlays 
    the network topology onto a map including optional river streams, 
    basins, and subbasins.

    Parameters:
    -----------
    graph : nx.DiGraph
        The directed graph containing station and dam data. Nodes must 
        contain 'lon' and 'lat' attributes for geographic positioning.
    nodes : Iterable
        A collection of node identifiers (IDs) to be included in the plot.
    labels : bool, default False
        If True, displays the node IDs as text labels on the map.
    streams : gpd.GeoDataFrame, optional
        Line geometries of the river network. If None, uses Natural Earth 
        physical features.
    basins : gpd.GeoDataFrame, optional
        Polygon geometries of the main river basin boundaries.
    subbasins : gpd.GeoDataFrame, optional
        Polygon geometries of the internal sub-watershed boundaries.
    **kwargs : dict
        Additional styling arguments:
        - figsize : tuple, default (12, 10)
        - title : str, optional
        - alpha : float, default 0.9
        - size : int, default 40 (base node size)
        - extent : list, [min_lon, max_lon, min_lat, max_lat]

    Returns:
    --------
    None
        Displays the resulting plot using matplotlib.
    """

    figsize = kwargs.get('figsize', (12, 10))
    title = kwargs.get('title', None)
    alpha = kwargs.get('alpha', .9)
    size = kwargs.get('size', 40)
    fontsize = kwargs.get('fontsize', 7)

    # Create the subgraph
    sub = graph.subgraph(nodes)

    # Define positions from our node attributes
    pos = {n: (data['lon'], data['lat']) for n, data in sub.nodes(data=True)}

    # Separate nodes by type for different styling
    stns = [ID for ID in sub.nodes() if 'station' in ID]
    color_stns = [attrs['strahler'] for ID, attrs in sub.nodes(data=True) if 'station' in ID]
    dams = [ID for ID in sub.nodes() if 'dam' in ID]
    color_dams = [attrs['strahler'] for ID, attrs in sub.nodes(data=True) if 'dam' in ID]
    outs = [ID for ID in sub.nodes() if 'outlet' in ID]

    # set up plot
    proj = ccrs.PlateCarree()
    fig, ax = plt.subplots(
        figsize=figsize, 
        subplot_kw={'projection': proj}
    )
    if 'extent' in kwargs:
            ax.set_extent(kwargs['extent'], crs=proj)
    ax.add_feature(
        cfeature.NaturalEarthFeature('physical', 'land', '10m', edgecolor='face', facecolor='wheat'),#'lightgray'),
        alpha=.5,
        zorder=0
    )
    if streams is None:
        ax.add_feature(
            cfeature.NaturalEarthFeature('physical', 'rivers_lake_centerlines', '10m', edgecolor='steelblue', facecolor='none', linewidth=.5),
            alpha=0.7,
            zorder=1
        )
    else:
        streams.plot(ax=ax, color='steelblue', linewidth=.5, alpha=.7, zorder=1)
    if subbasins is not None:
        subbasins.boundary.plot(ax=ax, edgecolor='k', lw=.25, ls=':', zorder=1)
    if basins is not None:
         basins.boundary.plot(ax=ax, edgecolor='k', lw=1, zorder=1)
    if title is not None:
        ax.text(.5, 1.025, title, horizontalalignment='center', verticalalignment='bottom', transform=ax.transAxes, fontsize=12)
    ax.axis('off')

    # Draw Edges
    nx.draw_networkx_edges(sub, pos, ax=ax, edge_color='dimgrey', 
                            width=1, arrows=True, arrowsize=5, alpha=alpha)

    # Draw Outlets
    nx.draw_networkx_nodes(sub, pos, nodelist=outs, ax=ax, 
                            node_color='indianred',# edgecolors='white', 
                            node_shape='x', node_size=size * .5,
                            label='Basin Outlet')

    # Draw Stations
    nx.draw_networkx_nodes(sub, pos, nodelist=stns, ax=ax, 
                            node_color=color_stns, cmap='viridis', edgecolors='white' , 
                            node_shape='o', node_size=size *.8,
                            label='Gauging Station')

    # Draw dams
    nx.draw_networkx_nodes(sub, pos, nodelist=dams, ax=ax, 
                            node_color=color_dams, cmap='viridis', edgecolors='white' , 
                            node_shape='v', node_size=size,
                            label='Dam')

    # Add Labels
    if labels:
        nx.draw_networkx_labels(sub, pos, font_size=fontsize, verticalalignment='bottom')

    ax.legend(loc=2, frameon=False)
    plt.tight_layout()

    plt.show()