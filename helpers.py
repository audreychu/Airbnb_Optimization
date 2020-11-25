import requests
import json
import pandas as pd
import numpy as np
import geopandas as gpd
from geopy import distance
from shapely.geometry import Point
import re

# Parameters for API request

client_id = 'TM1TQ4JBSFB0GDV3RG55DKJQL5WMQMTS4NNJVEONXLYIGKAQ'
client_secret = 'BRNKK4FLRIPRFK1XZK2DGD45YGIJYF45X1OKIMGQQHGXODA2'

url = 'https://api.foursquare.com/v2/venues/explore'
params = dict(
    client_id = client_id,
    client_secret = client_secret,
    v = '20201113',
    # near = 'New York, NY', # Can be more specific to best augment our neighborhoods dataset
    # radius = _             Another option to restrict our area of search
    limit = 50,
    sortByPopularity = 1 # Boolean mask to sort by popularity
)

def get_cleaned_foursquare_data(near, categoryId = None):
    """
    Get data from foursquare API for a given location and return relevant
    columns as dataframe with neighborhood label and popularity rank
    """

    params['near'] = near
    params['categoryId'] = categoryId
    response = requests.get(url=url, params=params)

    try:
        df = pd.json_normalize(json.loads(response.text)['response']['groups'][0]['items'])
    except KeyError:
        return(None)

    df = df.iloc[:, 3:10]
    df['neighborhood'] = near
    df['pop_rank'] = df.index + 1

    return(df)

def clean_latlon(df, lon_col, lat_col):
    """Clean lon/lat data for conversion to GeoDataFrame"""
    p = re.compile(r'[^\-\d\.]')
    df[lon_col] = [p.sub('', x) for x in df[lon_col].astype(str)]
    df[lat_col] = [p.sub('', x) for x in df[lat_col].astype(str)]

    df[lon_col] = df[lon_col].astype(float)
    df[lat_col] = df[lat_col].astype(float)

    return(df.rename(columns = {lon_col: 'longitude', lat_col: 'latitude'}))

def to_gdf(df):
    """Add point geometry to a given dataframe using cleaned lon/lat"""
    geometry = [Point(xy) for xy in zip(df.longitude, df.latitude)]
    gdf = gpd.GeoDataFrame(df, crs='epsg:4326', geometry = geometry)
    return(gdf)

def filter_to_neighbourhood(points, neigh, neighbourhoods_gdf):
    """Filter point data by neighborhood (to be used if neighbourhood
    is not already a label in dataframe)"""
    return(gpd.sjoin(points,
                     neighbourhoods_gdf.loc[neighbourhoods_gdf.neighbourhood == neigh],
                     how = 'inner', op='intersects'))

def filter_to_radius(geo_listing, points, radius_meters):
    """Filter data to all points (of a given dataframe) that are
    within a specified radius (in meters) of a given listing"""
    listing_proj = gpd.GeoDataFrame(geometry = [geo_listing['geometry']], crs = 'epsg:4326').to_crs('epsg:32118')

    buff = gpd.GeoDataFrame(geometry = [listing_proj.buffer(radius_meters).unary_union], crs = 'epsg:32118')

    points_proj = points.to_crs('epsg:32118')
    selected = gpd.sjoin(points_proj, buff, how = 'inner', op = 'within') # within much faster than intersects
    return(selected)

def idw_popularity(geo_listing, poi_gdf, citywide = 0, metric = 'sum'):
    """
    Calculate an index to measure closeness of a given listing to the
    most popular venues in its neighborhood. This is influenced by the
    inverse distance weighting method and intended to be used in a pandas apply
    chain
    """

    listing_proj = gpd.GeoDataFrame(geometry = [geo_listing['geometry']], crs = 'epsg:4326')

    if citywide == 0:
        neighborhood = geo_listing['neighbourhood_cleansed']
        if neighborhood not in poi_gdf.neighborhood.unique():
            neighborhood = geo_listing['neighbourhood_group_cleansed']
    else:
        neighborhood = 'New York City'

    geom = geo_listing['geometry']

    pois_select = poi_gdf.loc[poi_gdf['neighborhood'] == neighborhood].to_crs('epsg:4326')
    poi_ranks = pois_select['pop_rank']

    dists_to_listing = [distance.distance((listing_proj.geometry.y[0], listing_proj.geometry.x[0]),
                        (point.y, point.x)).km for point in pois_select['geometry']]
    id_pop_weights = [1/(x*y) for x,y in zip(poi_ranks, dists_to_listing)]

    if metric == 'sum':
        res = np.sum(id_pop_weights)
    if metric == 'mean':
        res = np.mean(id_pop_weights)

    return(res)

def get_closest_n_points(geo_listing, points, n, radius):
    """
    Return the closest n points to a given listing from a points GeoDataFrame
    """
    # Filter to radius to reduce computation:
    rad = filter_to_radius(geo_listing, points, radius)

    listing_proj = gpd.GeoDataFrame(geometry = [geo_listing['geometry'][0]], crs = 'epsg:4326')
    dists_to_listing = [distance.distance((listing_proj.geometry.y[0], listing_proj.geometry.x[0]),
                        (point.y, point.x)).km for point in rad['geometry']]

    res = rad.set_index(np.argsort(dists_to_listing), append = True).sort_index(level = 1).reset_index(1, drop = True).iloc[0:n]

    return(res)

def dist_to_closest(geo_listing, points):
    """Return the distance (in km) from listing to closest point in provided
    points dataframe"""

    listing_proj = gpd.GeoDataFrame(geometry = [geo_listing['geometry'][0]], crs = 'epsg:4326')
    dists_to_listing = [distance.distance((listing_proj.geometry.y[0], listing_proj.geometry.x[0]), (point.y, point.x)).km for point in points['geometry']]

    min_dist = np.min(dists_to_listing)
    return(min_dist)
