import requests
import json
import pandas as pd
import numpy as np
import geopandas as gpd
import geopy
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

def get_cleaned_foursquare_data(near):
    """
    Get data from foursquare API for a given location and return relevant
    columns as dataframe with neighborhood label and popularity rank
    """

    params['near'] = near
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
    p = re.compile(r'^[^\-] + [\d\.]$')
    df[lon_col] = [p.sub('', x) for x in df[lon_col].astype(str)]
    df[lat_col] = [p.sub('', x) for x in df[lat_col].astype(str)]

    df[lon_col] = df[lon_col].astype(float)
    df[lat_col] = df[lat_col].astype(float)

    return(df.rename(columns = {lon_col: 'longitude', lat_col: 'latitude'}))

def to_geodf(df):
    """Add point geometry to a given dataframe using cleaned lon/lat"""
    geometry = [Point(xy) for xy in zip(df.longitude, df.latitude)]
    gdf = gpd.GeoDataFrame(df, crs={'init': 'epsg:4326'}, geometry = geometry)
    return(gdf)

def filter_neighbourhood(points, neigh, neighbourhoods_gdf):
    """Filter point data by neighborhood (to be used if neighbourhood
    is not already a label in dataframe)"""
    return(gpd.sjoin(points,
                     neighbourhoods_gdf.loc[neighbourhoods_gdf.neighbourhood == neigh],
                     how = 'inner', op='intersects'))

def filter_radius(point, points, radius):
    """Filter data to all points (of a given dataframe) that are
    within a specified radius (in meters) of a given point"""

    point_proj = point.to_crs({'init': 'epsg:32118'})
    points_proj = points.to_crs({'init': 'epsg:32118'})

    buff = gpd.GeoDataFrame(geometry = [point_proj.buffer(radius).unary_union],
                            crs = {'init': 'epsg:32118'})
    selected = gpd.sjoin(points_proj, buff, how = 'inner', op = 'intersects')

    return(selected)

def idw_popularity(geo_listing, poi_gdf, neighborhood):
    """
    Calculate an index to measure closeness of a given listing to the
    most popular venues in its neighborhood. This is influenced by the
    inverse distance weighting method and intended to be used in a pandas apply
    chain
    """
