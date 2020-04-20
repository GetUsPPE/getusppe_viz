# import data and packages
import json, requests
import configparser
import os, sys, time
import os.path as path

# computing
import pandas as pd
pd.options.display.max_rows = 100
pd.options.display.max_columns = 200
import numpy as np

# Import local libraries
from geocode import geocoder
from mapping import choropleth_mapbox_usa_plot, \
    viz_correlation_ppe_request_covid19_cases, \
    choropleth_mapbox_layered_plot
from data_download import download_findthemasks_data, \
    download_nytimes_data, \
    download_hospital_data, \
    download_PPE_donors, \
    download_zip_to_fips_data, \
    download_ideo_merged_data
from data_process import add_fips_county_info_v2, \
    requests_per_county, \
    download_county_geojson_and_merge_df, \
    merge_covid_ppe_df, \
    process_hospital_data, \
    merge_covid_ppe_hosp_df, \
    calculate_covid_per_bed_available, \
    find_counties_with_covid19_and_no_ppe_request, \
    add_all_ppe_requests_to_merged_df, \
    add_fips_ppe_donors, \
    donors_per_county, \
    calculate_donor_per_requester, \
    create_requestor_df_for_querying_requesters, \
    calculate_covid_cases_per_ppe_request


def create_configs(file_location):
    config = configparser.ConfigParser()
    config.read(file_location)
    return config


if __name__ == '__main__':
    # Pull configs from src folder (i.e. current folder)
    config = create_configs(
        path.abspath(path.join('config.ini')))

    # Which dataset to download
    if str(config['viz']['find_the_masks_data_download_flag']) == True:
        print ('Find The Masks Dataset downloading')
        #Download find the mask data and convert to pandas
        mask_df = download_findthemasks_data(
            url = str(config['viz']['findthemasks_url']),
            request_headers = eval(config['viz']['request_headers']), 
            write_out_csv = False)
            
        # Create geocoder class to find fips and county information by lat/long
        geocoder = geocoder(str(config['viz']['county_fips_download_url']))
        
        #Search and add the FIPS code to each row - Will take a minute
        mask_df = add_fips_county_info_v2(mask_df, geocoder)
    else:
        # TODO: This will be the pull from the main GetUsPPE database in the future 
        print ('Ideo Merged Dataset downloading')
        # download zip to fips
        zip_fips_df=download_zip_to_fips_data()
        
        # Pull the ideo merged dataset
        mask_df = download_ideo_merged_data(
            url = str(config['viz']['ideo_url']), 
            zip_fips_df = zip_fips_df, 
            write_out_csv = False)

    # Sum amount of requests per county
    mask_df_counties = requests_per_county(mask_df, write_out_csv = False)

    # Download county geo information and merge
    counties, merged_df = download_county_geojson_and_merge_df(
        str(config['viz']['geojson_url']), mask_df_counties)
    merged_df = add_all_ppe_requests_to_merged_df(mask_df,merged_df)

    # Map the county level demand for PPE
    print ('Creating and saving map of ppe demand per county')
    choropleth_mapbox_usa_plot(
        counties = counties,
        locations = merged_df.fips,
        z = merged_df.PPE_requests,
        text = merged_df.ppe_text,
        #colorscale = ["#fdfcef", "#c7e9b4", "#6ab7a6","#41b6c4","#2c7fb8","#253494"],
        colorscale = ["#fdfcef","#c7e9b4","#D2FBFF","#36A2B9","#004469"],
        zmin = 0,
        zmax=10,
        title = ('PPE Requests By County - %s - (Hover for breakdown)' % time.strftime("%Y%m%d")),
        colorbar_title = '> PPE Requests',
        html_filename = '../img/PPE_Requests_By_County.html',
        show_fig=False)

    # Donwload COVID19 Data from NYTimes and covert to Pandas
    print ('Downloading NYtimes dataset')
    ny_times_covid_date=str(config['viz']['ny_times_covid_date'])
    covid_df = download_nytimes_data(
        url = str(config['viz']['ny_times_county_data_url']),
        date = ny_times_covid_date,
        write_out_csv = False)

    # Merge the covid and NYTimes data
    merged_covid_ppe_df=merge_covid_ppe_df(covid_df,merged_df) 

    # Map Covid cases and
    print ('Creating and saving map of Covid Cases and Deaths per county')
    choropleth_mapbox_usa_plot(
        counties = counties,
        locations = merged_covid_ppe_df.fips,
        z = merged_covid_ppe_df.cases,
        text = merged_covid_ppe_df.covid_text,
        colorscale = ["#fdfcef","#ffda55","#FFC831","#fc7555","#e96e81",],
        zmin = 0,
        zmax=500,
        title = ('COVID19 Cases Per County - %s - (Hover for breakdown)' % ny_times_covid_date),
        html_filename = ('../img/COVID19_Cases_Per_County_%s.html' % ny_times_covid_date),
        colorbar_title = '> COVID19 Cases',
        show_fig=False
    )

    # Download Hospital dataset
    print ('Downloading Hopsital Dataset')
    hospital_df = download_hospital_data(
        str(config['viz']['hospital_download_url']),
        write_out_csv = False)

    # Add county level infromation to hosptial beds
    hospital_df_counties = process_hospital_data(hospital_df, write_out_csv = False)

    # Merge in hospital data to covid and ppe data
    merged_covid_ppe_hosp_df=merge_covid_ppe_hosp_df(hospital_df_counties,merged_covid_ppe_df) 

    # Calculate covid cases per bed available
    merged_covid_ppe_hosp_df = calculate_covid_per_bed_available(merged_covid_ppe_hosp_df)

    # Calculate covid cases per ppe request
    merged_covid_ppe_hosp_df = calculate_covid_cases_per_ppe_request(merged_covid_ppe_hosp_df) 

    print ('Mapping covid19 hazard index by cases and bed availability')
    choropleth_mapbox_usa_plot(
        counties = counties,
        locations = merged_covid_ppe_hosp_df.fips,
        z = merged_covid_ppe_hosp_df.Covid_cases_per_bed,
        text = merged_covid_ppe_hosp_df.hosp_text,
        colorscale = ["#fdfcef","#ffda55","#FFC831","#fc7555","#e96e81",],
        zmin = 0,
        zmax=1,
        title = ('Hazard Ratio: Covid19 Cases, Per Bed, Per County - %s - (Hover for breakdown)' % ny_times_covid_date),
        html_filename = ('../img/Covid19_cases_per_bed_per_county_%s.html' % time.strftime("%Y%m%d")),
        colorbar_title = '> Hazard Ratio (Cases/Bed)',
        show_fig=False
        )

    print ('Creating Main Index.html with each choropleth map as a layer')
    choropleth_mapbox_layered_plot(counties = counties, html_filename = '../index.html',
        locations_0 = merged_df.fips,
        z_0 = merged_df.PPE_requests,
        text_0 = merged_df.ppe_text,
        colorscale_0 = ["#fdfcef","#c7e9b4","#D2FBFF","#36A2B9","#004469"],
        zmin_0 = 0,
        zmax_0 = 10,
        title_0 = ('PPE Requests By County - %s - (Hover for breakdown)' % time.strftime("%Y%m%d")),
        colorbar_title_0 = '> PPE Requests',
                                   
        locations_1 = merged_covid_ppe_df.fips,
        z_1 = merged_covid_ppe_df.cases,
        text_1 = merged_covid_ppe_df.covid_text,
        colorscale_1 = ["#fdfcef","#ffda55","#FFC831","#fc7555","#e96e81",],
        zmin_1 = 0,
        zmax_1=500,
        title_1 = ('COVID19 Cases Per County - %s - (Hover for breakdown)' % ny_times_covid_date),
        colorbar_title_1 = '> COVID19 Cases',
                                                 
        locations_2 = merged_covid_ppe_hosp_df.fips,
        z_2 = merged_covid_ppe_hosp_df.Covid_cases_per_PPE_requests,
        text_2 = merged_covid_ppe_hosp_df.covid_ppe_text,
        colorscale_2 =  ["#b5b5b5","#fae1ac","#ffcf69","#fab92f","#ffad00","#ff7700"],
        zmin_2 = 0,
        zmax_2 = 500,
        title_2 = ('Covid19 Cases, Per PPE Request, Per County - Counties with no PPE Requests are Default Gray - %s - (Hover for breakdown)' % ny_times_covid_date),
        colorbar_title_2 = '> Covid19 Cases Per Bed)',
                                   
        locations_3 = merged_covid_ppe_hosp_df.fips,
        z_3 = merged_covid_ppe_hosp_df.Covid_cases_per_bed,
        text_3 = merged_covid_ppe_hosp_df.hosp_text,
        colorscale_3 =  'Viridis',
        zmin_3 = 0,
        zmax_3 = 1,
        title_3 = ('Covid19 Cases, Per Hospital Bed, Per County (i.e. Potential PPE Need Hazard Index) - %s - (Hover for breakdown)' % ny_times_covid_date),
        colorbar_title_3 = '> Covid19 Cases Per Bed)',
        )



    print ('create_figures.py <> Finished')







