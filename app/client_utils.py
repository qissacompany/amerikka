#example client util functions
import streamlit as st
import pandas as pd
import geopandas as gpd
import h3pandas as h3
from shapely.geometry import box, Point
import requests
from requests.structures import CaseInsensitiveDict
import json
import geocoder
from faker import Faker
import boto3
import osmnx as ox
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


#client keys
reach_url = st.secrets['reach']['REACH_url']
reach_key = st.secrets['reach']['REACH_client_key']
bucket_key = st.secrets["client_bucket"]['BUCKET_idkey']
bucket_secret = st.secrets["client_bucket"]['BUCKET_secretkey']
bucket_url = st.secrets["client_bucket"]['BUCKET_url']
bucket_name = st.secrets["client_bucket"]['BUCKET_name']
px.set_mapbox_access_token(st.secrets["mapbox"]['MAPBOX_client_token'])
client_style = st.secrets['mapbox']['MAPBOX_qissa_default'] #or MAPBOX_client_tiles if defined for client


#get classificator json
def get_classificator_json():
    file_name = 'classifiers/osm_cls_v1.json'
    s3_client = boto3.client('s3', endpoint_url=f"https://{bucket_url}",
                                      aws_access_key_id=bucket_key,
                                      aws_secret_access_key=bucket_secret)
    obj = s3_client.get_object(Bucket=bucket_name, Key=file_name)
    # Read the content of the file and decode it
    content = obj['Body'].read().decode('utf-8')
    # Parse the JSON content
    categories = json.loads(content)
    return categories


#get isolines as h3
def reach_h3(latlng,mode="transit",reso=9,times=[5,10,15,20],reid_list=None):
    start_time = time.time()
    def get_isoline_gdf(latlng,time=600,mode='transit',reid=None, apiKey=reach_key):
        # query
        url_base = reach_url
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        if reid is not None:
            REID_PARAMS = {
                'apiKey': apiKey,
                'id':reid,
                }
            resp = requests.get(url_base, headers=headers, params=REID_PARAMS)
        else:
            REQUEST_PARAMS = {
                'apiKey': apiKey,
                'lat':latlng[0],
                'lon':latlng[1],
                'type':'time',
                'mode':mode, #drive,bicycle,mountain_bike,walk,hike,transit,approximated_transit
                'range':time,
                #'traffic':
                #'route_type':
                #'avoid':
                }
            resp = requests.get(url_base, headers=headers, params=REQUEST_PARAMS)
        
        #geodateframe
        isoline_gdf = gpd.read_file(resp.text, driver='GeoJSON')
        reid = isoline_gdf['id'].values[0]
        return isoline_gdf, reid
    
    # loop intervals
    time_intervals = []
    for t in times:
        time_intervals.append(t*60) #in seconds

    #list to store isolines
    isolines = []

    #loop time intervals OR reid_list
    if reid_list is not None:
        for re_id in reid_list:
            isoline_gdf,re_id = get_isoline_gdf(reid=re_id)
            isoline_gdf['time'] = isoline_gdf['range']/60 #minutes
            #add h3 polyfill hexas as index
            isoline = isoline_gdf.h3.polyfill(reso, explode=True).set_index('h3_polyfill')
            isolines.append(isoline)
    else:
        reid_list = []
        for interval in time_intervals:
            isoline_gdf,reid = get_isoline_gdf(latlng,time=interval,mode=mode)
            isoline_gdf['time'] = isoline_gdf['range']/60 #minutes
            #add h3 polyfill hexas as index
            isoline = isoline_gdf.h3.polyfill(reso, explode=True).set_index('h3_polyfill')
            isolines.append(isoline)
            # save reid in list
            reid_list.append(reid)
    
    gdf_isolines = pd.concat(isolines)

    #replace geometries with geoms of h3 hexa
    h3_isolines = gdf_isolines.h3.h3_to_geo_boundary()

    # remove overlaps
    h3_isolines = h3_isolines[~h3_isolines.index.duplicated(keep='first')]

    #rename index
    h3_out = h3_isolines[['mode','time','lat','lon','geometry']]
    h3_out.index.rename('h3_id', inplace=True)

    print("Done in %s seconds" % (time.time() - start_time))

    return h3_out #, reid_list



# plot h3 isolines
def reach_map_plot(gdf,latlng,lin=0,color='time',zoom=12,height=900):
    #LOCAT
    travel_time = ['Matka-aika','Travel time']

    #center
    lat = latlng[0]
    lon = latlng[1]

    #scale cirle
    # Create a GeoDataFrame with the center point in EPSG:4326
    center_gdf = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs="EPSG:4326")
    # Transform to EPSG:3067
    center_gdf = center_gdf.to_crs("EPSG:3067")
    # Create a circle with 1km radius in EPSG:3067
    circle = center_gdf.iloc[0].geometry.buffer(500)
    # Create a GeoDataFrame with the circle geometry and transform back to EPSG:4326
    ring = gpd.GeoDataFrame(geometry=[circle], crs="EPSG:3067").to_crs("EPSG:4326")

    #colors
    gdf['time'] = gdf['time'].astype(str)
    time_colors = {
        '10.0':'brown',
        '15.0':'chocolate',
        '20.0':'goldenrod',
        '25.0':'burlywood',
        '30.0':'antiquewhite'
    }
    
    fig = px.choropleth_mapbox(gdf,
                                geojson=gdf.geometry,
                                locations=gdf.index,
                                color=color,
                                hover_name='time',
                                center={"lat": lat, "lon": lon},
                                mapbox_style=client_style,
                                color_discrete_map=time_colors,
                                labels={'time':travel_time[lin]},
                                zoom=zoom,
                                opacity=0.5,
                                width=1200,
                                height=height
                                )
    #add scale ring
    if ring is not None:
        fig.update_layout(
            mapbox={
                "layers": [
                    {
                        "source": json.loads(ring.to_crs(4326).to_json()),
                        "type": "line",
                        "color": "black",
                        "line": {"width": 0.5, "dash": [5, 5]},
                    }
                ]
            }
        )

    #legend and margin
    fig.update_layout(margin={"r": 10, "t": 50, "l": 10, "b": 10},
                                    legend=dict(
                                        yanchor="top",
                                        y=0.99,
                                        xanchor="left",
                                        x=0.01
                                    )
                                    )
    fig.update_traces(marker_line_width=0)
    for trace in fig.data:
        trace.hoverinfo = 'none'
        
    return fig


def osm_pois_for_h3(_h3_df, categories_json, lin=0):
    # convert h3 to polygon
    df = _h3_df.h3.h3_to_geo_boundary()
    
    # Select the language for the classification
    lang_key = 'FIN' if lin == 0 else 'ENG'
    
    # Create columns for each category in the selected language
    for category, values in categories_json.items():
        df[values[lang_key]] = 0  # Initialize the category count as 0
    
    pois_list = []

    #init progress bar
    progress_bar = st.progress(0)
    progress_increment = 100.0 / len(df)
    current_progress = 0
    
    # Fetch and classify POIs for each hexagon
    for index, row in df.iterrows():
        #update bar
        current_progress += progress_increment
        progress_bar.progress(int(current_progress))

        hex_time = row['time']
        
        # Fetch POIs using osmnx
        try:
            pois_gdf = ox.geometries_from_polygon(row['geometry'], tags={'amenity': True, 'shop': True, 'leisure': True}).reset_index()
        except Exception as e:
            print(f"Error fetching POIs: {e}")
            pois_gdf = None
        
        # Classify the POIs
        if pois_gdf is not None:
            for _, poi_row in pois_gdf.iterrows():
                for category, values in categories_json.items():
                    # Check if 'amenity' column contains the values/tags
                    if 'amenity' in poi_row and poi_row['amenity'] in values['tags']:
                        # Get the correct language category name
                        category_name = values[lang_key]
                        df.at[index, category_name] += 1
                        # Append to POI list
                        pois_list.append({
                            'name': poi_row.get('name', None),
                            'category': category_name,
                            'time': hex_time
                        })

    # bar to 100
    progress_bar.progress(100)

    # Drop the geometry column
    df.drop(columns=['geometry'], inplace=True)
    # Group by time
    grouped_sums = df.groupby('time').sum().reset_index()

    return grouped_sums, pois_gdf


#plot service profile by time
def plot_amenity_profile(amenity_reach_h3,lin=0):
    #LOCAT
    plot_title = ['Palveluprofiili','Service profile']
    industry_classes = ['Toimialat','Service types']
    x_title = ['Kävelyaika','Walking time']
    y_title = ['Palveluiden määrä','Number of services']
    amenity_fig = px.line(amenity_reach_h3, x='time', y=amenity_reach_h3.columns, title=plot_title[lin])
    amenity_fig.update_layout(
                    legend_title_text=industry_classes[lin], 
                    xaxis_title=x_title[lin],
                    yaxis_title=y_title[lin]
                )
    amenity_fig.update_xaxes(tickvals=amenity_reach_h3['time'].unique())

    return amenity_fig