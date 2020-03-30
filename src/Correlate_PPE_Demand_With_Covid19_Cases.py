#!/usr/bin/env python
# coding: utf-8

# Correlation of PPE Demand in USA With Covid19 Cases

# import data
import json
import time
import requests
from io import StringIO
import os

# computing
import pandas as pd
import numpy as np
from tqdm.auto import tqdm

# Import geopandas package
import geopandas as gpd
import reverse_geocoder as rg
import addfips
import plotly.figure_factory as ff
import plotly.graph_objects as go

# plotting
import plotly.express as px
import plotly.graph_objects as go


# ## Configs
findthemasks_url = 'http://findthemasks.com/data.json'
request_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"}
county_fips_download_url = 'https://github.com/ShyamW/Geocoding_Suite/blob/master/Lat_Lng_to_County_Data/county_Fips.txt'
geojson_url = 'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'
ny_times_covid_date = '2020-03-27'
ny_times_county_data_url = 'https://github.com/nytimes/covid-19-data/raw/master/us-counties.csv'
# Import hospital information compiled by https://beta.covidmap.link/
hospital_download_url = 'https://docs.google.com/spreadsheet/ccc?key=15gZsozGQp-wdJaSngvLV13iCf_2mm2IsZpHOPxZtvtI&output=csv'

def download_findthemasks_data(url,request_headers):
    # Download the data
    s=requests.get(url, headers= request_headers).text

    # Extract the json format, and find column headers
    json_data = json.loads(s)
    HEADERS = json_data['values'][0]

    # create the data frame
    mask_df = pd.DataFrame.from_dict(json_data['values'][2:])
    mask_df.columns=HEADERS
    
    # Using DataFrame.drop
    mask_df = mask_df.dropna(how='any', subset=['Lat', 'Lng'])

    # Rename the State? column
    mask_df.rename(columns={'State?': 'State'}, inplace=True)

    # Drop institutions with multiple entries
    mask_df.drop_duplicates(subset='What is the name of the hospital or clinic?', inplace=True)

    return mask_df

mask_df = download_findthemasks_data(url = findthemasks_url, request_headers = request_headers)
mask_df.head(2)

class geocoder:
    def __init__(self, county_fips_download_url):
        self.af = addfips.AddFIPS()
        self.download_county_fips_info(county_fips_download_url)
        
    def download_county_fips_info(self, url):
        contents=requests.get(url).text
        with open('county_Fips.txt', 'w') as f:
            f.write(contents)    
        
    def fips_code_lookup(self, county, state):
        # Lookup of fips code (https://github.com/fitnr/addfips)
        fips = self.af.get_county_fips(county, state)
        return fips

    def get_geocoder_info_from_rg(self, Lat, Lng):
        try:
            # Reverse geocoder api call to get county name
            coordinates = (Lat, Lng)
            results = rg.search(coordinates) # default mode = 2
            county = results[0]['admin2']
            state = results[0]['admin1']

            # Lookup of fips code (https://github.com/fitnr/addfips)
            fips = self.fips_code_lookup(county,state)

            # return the fip and county
            return {'fips':fips, 'county':county}
        except ValueError:
            return {'fips':'NA', 'county':'NA'}


# ### Search and add the FIPS code to each row - WILL TAKE SEVERAL MINS
def add_fips_county_info(mask_df, geocoder):
    # Start tdqm timer from tqdm.auto
    tqdm.pandas()

    # Reverse geocoder used to get geocoded fips and county information
    # Note: Progress_apply is used for the timer functionality
    mask_df['geocoder'] = mask_df.progress_apply(
        lambda x: geocoder.get_geocoder_info_from_rg(x['Lat'], x['Lng']), axis=1)

    # Map the geocoder dict column to individual columns
    mask_df['fips'] = mask_df.apply(
        lambda x: x['geocoder']['fips'], axis=1)
    mask_df['county'] = mask_df.apply(
        lambda x: x['geocoder']['county'], axis=1)
    mask_df.drop(columns=['geocoder'],inplace = True)

    # Using DataFrame.drop to remove any fips code that could not be mapped
    mask_df = mask_df.dropna(how='any', subset=['fips','county'])
    
    return mask_df

geocoder = geocoder(county_fips_download_url)
mask_df = add_fips_county_info(mask_df, geocoder)


# ### Sum amount of requests per county
def requests_per_county(mask_df, write_out_csv = True):
    # Count the amount of requests per county
    mask_df_counties=mask_df.groupby(['fips','county']).size().reset_index(name='counts')
    
    # write out this data file to csv
    if write_out_csv:
        timestr = time.strftime("%Y%m%d")
        path = 'findthemasks_data_processed_' + timestr + '.csv'
        mask_df.to_csv (path, index = False, header=True)

        ##### TODO
        # Some of the data written out is corrupted and misaligned by row
        # Not sure what the bug is right now
    
    return mask_df_counties


mask_df_counties = requests_per_county(mask_df, write_out_csv = True)
mask_df_counties.head(5)


# ### Download county geo information
def download_county_geojson(geojson_url):
    # Download the data
    s=requests.get(geojson_url).text

    # Extract the json format, and find column headers
    counties = json.loads(s)
    return counties


counties = download_county_geojson(geojson_url)


# ### Map PPE requests by County
def choropleth_mapbox_usa_plot (counties, locations, z, text,
                                colorscale = "RdBu_r", zmin=-1, zmax=10, title='choropleth_mapbox_usa_plot'):
    
    # Choropleth graph. For reference: https://plotly.com/python/mapbox-county-choropleth/
    fig = go.Figure(go.Choroplethmapbox(
        geojson=counties, locations=locations, z=z, text=text,
        colorscale=colorscale,zmin=zmin,zmax=zmax,marker_opacity=0.5, 
        marker_line_width=0, 
        ))
    
    # Center on US
    fig.update_layout(
        title=title,
        mapbox_style="carto-positron",
        mapbox_zoom=3, 
        mapbox_center = {"lat": 37.0902, "lon": -95.7129},
        margin={"r":0,"t":30,"l":0,"b":0})
    fig.show()

    
choropleth_mapbox_usa_plot(
    counties = counties,
    locations = mask_df_counties.fips,
    z = mask_df_counties.counts,
    text = mask_df_counties.county,
    colorscale = "RdBu_r",
    zmin = -1,
    zmax=10,
    title = 'PPE Requests By County')


# ## Download COVID19 data and convert to pandas
def download_findthemasks_data(url, date, write_out_csv = True):
    covid_df = pd.read_csv(url)
    covid_df = covid_df.loc[covid_df['date'] == date]

    # NYC data is missing county, so make them all New York County.
    covid_df.loc[covid_df['county'] == 'New York City', 'fips'] = '36061'
    # Kansas City data is missing the specific county so make them all Cook County
    covid_df.loc[(covid_df['county'] == 'Kansas City') & 
              (covid_df['state'] == 'Missouri'), 'fips'] = '29095'
    
    # drop the rows without a fips value
    covid_df = covid_df.dropna(how='any', subset=['fips'])

    # convert to int to remove the decimal values
    covid_df['fips'] = covid_df['fips'].apply(int)
    
    # Zfill all countyFIPS to be 5 characters
    width=5
    covid_df["fips"]= covid_df["fips"].astype(str)
    covid_df["fips"]= covid_df["fips"].str.zfill(width) 
    
    # write out this data file to csv
    if write_out_csv:
        timestr = time.strftime("%Y%m%d")
        path = 'COVID19_nytimes_' + date + ' data_processed_on_' + timestr + '.csv'
        covid_df.to_csv (path, index = False, header=True)
    
    return covid_df
    
covid_df = download_findthemasks_data(ny_times_county_data_url, ny_times_covid_date, write_out_csv = True)
covid_df.head(5)


choropleth_mapbox_usa_plot(
    counties = counties,
    locations = covid_df.fips,
    z = covid_df.cases,
    text = covid_df.county,
    colorscale = "RdBu_r",
    zmin = -1,
    zmax=100,
    title = ('COVID19 Cases Per County:%s' % ny_times_covid_date))


# ## Hospital bed visualization by county 
def download_hospital_data(url, write_out_csv = True):
    hospital_df = pd.read_csv(hospital_download_url)
    # Start tdqm timer from tqdm.auto
    tqdm.pandas()

    # Reverse geocoder used to get geocoded fips and county information
    # Note: Progress_apply is used for the timer functionality
    hospital_df['fips'] = hospital_df.progress_apply(
        lambda x: geocoder.fips_code_lookup(x['COUNTY'], x['STATE']), axis=1)
    
    # clean the BEDS column to make sure all are positive in value, by converting negative beds to 0
    hospital_df.sort_values(by=['BEDS'], ascending=False, inplace=True)
    hospital_df['BEDS'][hospital_df['BEDS'] < 0] = 0
    
    # write out this data file to csv
    if write_out_csv:
        timestr = time.strftime("%Y%m%d")
        path = 'hospital_data_processed_' + timestr + '.csv'
        mask_df.to_csv (path, index = False, header=True)

    return hospital_df


hospital_df = download_hospital_data(hospital_download_url, write_out_csv = True)
hospital_df.head(3)


def process_hospital_data(hospital_df, write_out_csv = True):
    # Sum the amount of beds per county
    hospital_df_counties = hospital_df.groupby(['fips','COUNTY'])['BEDS'].sum().reset_index()

    # write out this data file to csv
    if write_out_csv:
        timestr = time.strftime("%Y%m%d")
        path = 'hospital_data_county_data_' + timestr + '.csv'
        mask_df.to_csv (path, index = False, header=True)
        
    return hospital_df_counties
    
    
hospital_df_counties = process_hospital_data(hospital_df, write_out_csv = True)
hospital_df_counties.head(2)


choropleth_mapbox_usa_plot(
    counties = counties,
    locations = hospital_df_counties.fips,
    z = hospital_df_counties.BEDS,
    text = hospital_df_counties.COUNTY,
    colorscale = "RdBu_r",
    zmin = -1,
    zmax=500,
    title = 'Hospital beds per county'
    )


# ### Covid cases per bed available
def calculate_covid_per_bed_available(covid_df, hospital_df_counties):
    # join the covid patients dataframe with the beds per county dataframe, on the fips index
    covid_per_bed_df = covid_df.join(hospital_df_counties.set_index('fips'), on='fips')
    
    # remove counties with 0 known bed numbers
    covid_per_bed_df = covid_per_bed_df[covid_per_bed_df.BEDS != 0]
    
    # calculate the covid patients per bed, adding the column that saves this info
    covid_per_bed_df['Covid_cases_per_bed'] = covid_per_bed_df.apply(
            lambda x: (x['cases'] / x['BEDS']), axis=1)
    
    # fill the NA in normalized_covid_patients_per_bedwith 0s
    covid_per_bed_df['Covid_cases_per_bed'].fillna(0, inplace=True)
    
    # sort by highest normalized_covid_patients_per_bed
    covid_per_bed_df.sort_values(by='Covid_cases_per_bed', ascending=False, inplace=True)
    
    return covid_per_bed_df


covid_per_bed_df = calculate_covid_per_bed_available(covid_df, hospital_df_counties)
covid_per_bed_df[['date','county','state','cases','deaths','BEDS','Covid_cases_per_bed']].head(20)

choropleth_mapbox_usa_plot(
    counties = counties,
    locations = covid_per_bed_df.fips,
    z = covid_per_bed_df.Covid_cases_per_bed,
    text = covid_per_bed_df.COUNTY,
    colorscale = "RdBu_r",
    zmin = 0,
    zmax=1,
    title = 'Covid cases per hospital bed - per county'
    )


# ### Counties without PPE requests, with highest Covid19 cases
def find_counties_with_covid19_and_no_ppe_request(covid_df, mask_df_counties):
    # join the covid patients dataframe with the beds per county dataframe, on the fips index
    covid_ppe_df = covid_df.join(
        mask_df_counties.set_index('fips'), on='fips',  how='left', lsuffix='_covid', rsuffix='_ppe')
    
    # fill the NA in normalized_covid_patients_per_bedwith 0s
    covid_ppe_df['counts'].fillna(0, inplace=True)
    
    # sort by highest normalized_covid_patients_per_bed
    covid_ppe_df.sort_values(by=['counts','cases'], ascending=(True, False), inplace=True)
    
    # change name of column 'counts' to 'PPE_requests' 
    covid_ppe_df.rename(inplace=True,
        columns={'counts':'PPE_requests', 'county_covid':'county'})
    
    return covid_ppe_df


covid_ppe_df = find_counties_with_covid19_and_no_ppe_request(covid_df, mask_df_counties)
covid_ppe_df[['date','county','state','cases','deaths','PPE_requests']].head(15)

# Select the counties that have no_ppe_requests and covid cases
counties_with_no_ppe_requests_and_covid_cases = covid_ppe_df[covid_ppe_df.PPE_requests == 0]

# Map covid cases in counties that do not have PPE requests
choropleth_mapbox_usa_plot(
    counties = counties,
    locations = counties_with_no_ppe_requests_and_covid_cases.fips,
    z = counties_with_no_ppe_requests_and_covid_cases.cases,
    text = counties_with_no_ppe_requests_and_covid_cases.county,
    colorscale = "RdBu_r",
    zmin = 0,
    zmax=100,
    title = 'Counties that have covid cases and 0 PPE requests'
    )


# ### Correlation of PPE request per county with COVID19 cases

# select counties that have had at least 1 ppe request
counties_with_ppe_requests_and_covid_cases = covid_ppe_df[covid_ppe_df.PPE_requests != 0]

# join with the dataframe that has covid cases per hospital bed
covid_ppe_df = counties_with_ppe_requests_and_covid_cases.join(
    covid_per_bed_df[['county','state','fips','Covid_cases_per_bed','BEDS',]].set_index('fips'),
    on='fips',  how='left', lsuffix='', rsuffix='_ppe')

# sort by highest normalized_covid_patients_per_bed
counties_with_ppe_requests_and_covid_cases.sort_values(by=['PPE_requests','cases'], ascending=False, inplace=True)
counties_with_ppe_requests_and_covid_cases[
    ['date','county','state','cases','deaths','BEDS','PPE_requests','Covid_cases_per_bed']].head(20)

fig = px.scatter(
    counties_with_ppe_requests_and_covid_cases,
    x=counties_with_ppe_requests_and_covid_cases.cases, 
    y=counties_with_ppe_requests_and_covid_cases.PPE_requests,
    color='Covid_cases_per_bed',
    log_x=True,
    #log_y=True,
    labels={
        'Covid_cases_per_bed':'Covid19 cases per hospital bed',
        'x':'Covid19 Cases Per County',
        'y':'PPE Requests Per County',
        'text':'County'
        },
    hover_name=counties_with_ppe_requests_and_covid_cases.county,
    range_color=(0,1),
    range_x=(1,30000)
    )

fig.update_layout(
    title = "Correlation of PPE request per county with COVID19 cases",
    #hoverlabel={'text'},
    )

#fig.update_xaxes(nticks=30)
#fig.update_yaxes(nticks=20)
    
fig.show()







