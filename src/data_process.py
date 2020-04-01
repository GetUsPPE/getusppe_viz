from geocode import geocoder
import pandas as pandas
import time
import requests
import json
import us

def requests_per_county(mask_df, write_out_csv = True):
    # Count the amount of requests per county
    mask_df_counties=mask_df.groupby(['fips','county','State']).size().reset_index(name='counts')
    
    # write out this data file to csv
    if write_out_csv:
        timestr = time.strftime("%Y%m%d")
        path = 'findthemasks_data_processed_' + timestr + '.csv'
        mask_df.to_csv (path, index = False, header=True)

        ##### TODO
        # Some of the data written out is corrupted and misaligned by row
        # Not sure what the bug is right now
    
    return mask_df_counties


def add_fips_county_info(mask_df, geocoder):
    print ('Pulling geocodes from Lat+Lng. This will take awhile...')
    mask_df['geocoder'] = mask_df.apply(
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


def download_county_geojson(geojson_url):
    # Download the data
    s=requests.get(geojson_url).text

    # Extract the json format, and find column headers
    counties = json.loads(s)
    
    # Create counties_df from geojson counties object
    counties_df = pd.DataFrame.from_dict(counties['features'])
    counties_df['properties'][0]

    # extract properties dict, then concatenate new clumsn and remove old properties column
    counties_df = pd.concat(
        [counties_df, pd.json_normalize(counties_df['properties'])], axis=1).drop(['properties'], axis=1)

    # clean up the dataframe                                                                               
    counties_df.drop(['type','COUNTY','LSAD'], axis=1, inplace=True)
    counties_df.rename(columns={'id':'fips','NAME':'county'}, inplace=True)
    counties_df.head()
    
    # join with the dataframe that has ppe requests: mask_df
    merged_df = counties_df.join(
        mask_df_counties[['fips','counts']].set_index('fips'),
        on='fips',  how='left', lsuffix='counties', rsuffix='mask_df')

    # fill the NA in counts with 0s
    merged_df['counts'].fillna(0, inplace=True)
    
    # change name of column 'counts' to 'PPE_requests' 
    merged_df.rename(inplace=True,
        columns={'counts':'PPE_requests'})
    
    # Map fips state code to state name
    merged_df['STATE'] = merged_df.progress_apply(
        lambda x: us.states.lookup(x['STATE']), axis=1)
    merged_df['county_info_for_map'] = merged_df.progress_apply(
        lambda x: ('PPE Requests: %s, %s'%(x['county'],x['STATE'])), axis=1)
    
    # Create text column for use in mapping
    merged_df['ppe_text'] = 'PPE Requests: ' + merged_df['PPE_requests'].astype(int).astype(str) + '<br>'+ \
        merged_df['county'].astype(str) + ', ' + merged_df['STATE'].astype(str)
    
    # return a json object called counties for plotting, and a counties_df for joins+manipulation of other data
    return counties, merged_df


def merge_covid_ppe_df(covid_df,merged_df): 
    merged_covid_ppe_df = merged_df.join(
        covid_df[['fips','cases','deaths']].set_index('fips'),
        on='fips',  how='left', lsuffix='merged', rsuffix='covid_df')
    
    # fill the NA in counts with 0s
    merged_covid_ppe_df['cases'].fillna(0, inplace=True)
    merged_covid_ppe_df['deaths'].fillna(0, inplace=True)
    
    # Create text column for use in mapping
    merged_covid_ppe_df['covid_text'] = merged_covid_ppe_df['county'].astype(str) + ', ' + \
        merged_covid_ppe_df['STATE'].astype(str) + '<br><br>'+\
        'Covid19: ' + '<br>'+ \
        'Cases: ' + merged_covid_ppe_df['cases'].astype(int).astype(str) + '<br>'+ \
        'Deaths: ' + merged_covid_ppe_df['deaths'].astype(int).astype(str) + '<br><br>'+ \
        'PPE Requests: ' + merged_covid_ppe_df['PPE_requests'].astype(int).astype(str)

    # TODO: Merge the counties geojson for all of new york
    '''
    print(counties['features'][0])

    # possibly leverage this code to merge polygons
    from shapely.geometry import Polygon
    from shapely.ops import cascaded_union

    polygon1 = Polygon([(0, 0), (5, 3), (5, 0)])
    polygon2 = Polygon([(0, 0), (3, 10), (3, 0)])

    polygons = [polygon1, polygon2]

    u = cascaded_union(polygons)
    '''
        
    return merged_covid_ppe_df


def process_hospital_data(hospital_df, write_out_csv = True):
    # Sum the amount of beds per county
    hospital_df_counties = hospital_df.groupby(['fips','COUNTY'])['BEDS'].sum().reset_index()

    # write out this data file to csv
    if write_out_csv:
        timestr = time.strftime("%Y%m%d")
        path = 'hospital_data_county_data_' + timestr + '.csv'
        hospital_df_counties.to_csv (path, index = False, header=True)
        
    return hospital_df_counties


def merge_covid_ppe_hosp_df(hospital_df_counties,merged_covid_ppe_df): 
    merged_covid_ppe_hosp_df = merged_covid_ppe_df.join(
        hospital_df_counties[['fips','BEDS']].set_index('fips'),
        on='fips',  how='left', lsuffix='merged', rsuffix='hospital')
    
    # fill the NA in counts with 0s
    merged_covid_ppe_hosp_df['BEDS'].fillna(0, inplace=True)
    
    # Create text column for use in mapping
    merged_covid_ppe_hosp_df['hosp_text'] = merged_covid_ppe_hosp_df['county'].astype(str) + ', ' + \
        merged_covid_ppe_hosp_df['STATE'].astype(str) + '<br><br>'+\
        'Hospital Beds: ' + merged_covid_ppe_hosp_df['BEDS'].astype(int).astype(str) + '<br>'+ \
        '<br>'+ \
        'Covid19: ' + '<br>'+ \
        'Cases: ' + merged_covid_ppe_hosp_df['cases'].astype(int).astype(str) + '<br>'+ \
        'Deaths: ' + merged_covid_ppe_hosp_df['deaths'].astype(int).astype(str) + '<br><br>'+ \
        'PPE Requests: ' + merged_covid_ppe_hosp_df['PPE_requests'].astype(int).astype(str)
        
    return merged_covid_ppe_hosp_df


# In order to avoid divide by zero problem in lambda function within calculate_covid_per_bed_available
def weird_division(n, d):
    return n / d if d else 0

def calculate_covid_per_bed_available(merged_covid_ppe_hosp_df):
    # calculate the covid patients per bed, adding the column that saves this info
    merged_covid_ppe_hosp_df['Covid_cases_per_bed'] = merged_covid_ppe_hosp_df.apply(
            lambda x: (weird_division(x['cases'], x['BEDS'])), axis=1)
    
    # sort by highest normalized_covid_patients_per_bed
    merged_covid_ppe_hosp_df.sort_values(by='Covid_cases_per_bed', ascending=False, inplace=True)
    
    # Create text column for use in mapping
    merged_covid_ppe_hosp_df['hosp_text'] = merged_covid_ppe_hosp_df['county'].astype(str) + ', ' + \
        merged_covid_ppe_hosp_df['STATE'].astype(str) + '<br><br>'+ \
        'HAZARD RATIO (Cases/Bed): ' + merged_covid_ppe_hosp_df['Covid_cases_per_bed'].astype(float).astype(str) + '<br><br>'+ \
        'Hospital Beds: ' + merged_covid_ppe_hosp_df['BEDS'].astype(int).astype(str) + '<br>'+ \
        '<br>'+ \
        'Covid19: ' + '<br>'+ \
        'Cases: ' + merged_covid_ppe_hosp_df['cases'].astype(int).astype(str) + '<br>'+ \
        'Deaths: ' + merged_covid_ppe_hosp_df['deaths'].astype(int).astype(str) + '<br><br>'+ \
        'PPE Requests: ' + merged_covid_ppe_hosp_df['PPE_requests'].astype(int).astype(str)
    
    return merged_covid_ppe_hosp_df


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
    
    ### TODO
    # There may be a mismatch of the PPE requests lat/long and those of the hospital data
    # since District of Columbia is appearing at the top, and that is unlikely
    
    return covid_ppe_df






