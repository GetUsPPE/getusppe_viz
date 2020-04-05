from geocode import geocoder
import pandas as pd
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
        mask_df_counties.to_csv (path, index = False, header=True)

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


def download_county_geojson_and_merge_df(geojson_url, mask_df_counties):
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
    merged_df['STATE'] = merged_df.apply(
        lambda x: us.states.lookup(x['STATE']), axis=1)
    merged_df['county_info_for_map'] = merged_df.apply(
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

def add_all_ppe_requests_to_merged_df(mask_df,merged_df):
    # get all fips code in the mask_df frame
    unique_fips=mask_df.fips.unique()

    for fip in unique_fips:
        # get all entries that have the same fip code and convert to dict, then string
        value = json.dumps(mask_df[mask_df['fips']==fip].to_dict())

        # select rows where the fips code equals fip
        merged_df.loc[merged_df['fips'] == str(fip),'all_ppe_requests']=value

        # fill the NA in normalized_covid_patients_per_bedwith 0s
        merged_df['all_ppe_requests'].fillna(0, inplace=True)
        
        # How to pull array of dicts from 'all_ppe_requests' category
        ''' 
        all_ppe_locations_array= eval(str(merged_df.loc[
            merged_df['fips'] == '01073', 'all_ppe_requests'].values))
        '''
        
    return merged_df


def add_fips_ppe_donors(ppe_donors_df, zip_fips_df):
    # zfill the fips to make sure they are right
    width=5
    zip_fips_df["fips"]= zip_fips_df["fips"].astype(str)
    zip_fips_df["fips"]= zip_fips_df["fips"].str.zfill(width) 
    zip_fips_df["zip"]= zip_fips_df["zip"].astype(str)
    zip_fips_df["zip"]= zip_fips_df["zip"].str.zfill(width) 
    
    # join the ppe_donors with the zip code to add fips, state, county info
    ppe_donors_with_zip_df = ppe_donors_df.join(zip_fips_df.set_index('zip'),
                                         how='left',on='zip', lsuffix='donors', rsuffix='zip')
    
    # Clean the data by dropping rows that are missing fips
    ppe_donors_with_zip_df = ppe_donors_with_zip_df.dropna(how='any', subset=['fips'])  
    
    # join the ppe_donors with the zip code to add fips, state, county info
    ppe_donors_with_zip_df = ppe_donors_with_zip_df.join(zip_lat_long_df.set_index('zip'),
                                         how='left',on='zip', lsuffix='donors', rsuffix='lat_lon')
    
    # Clean the data by dropping rows that are missing lat lon
    ppe_donors_with_zip_df = ppe_donors_with_zip_df.dropna(how='any', subset=['lat'])  
    
    return ppe_donors_with_zip_df

def donors_per_county(ppe_donors_with_zip_df, 
    merged_covid_ppe_hosp_df, write_out_csv = True):
    # Count the amount of requests per county
    donors_df_counties=ppe_donors_with_zip_df.groupby(['fips']).size().reset_index(name='ppe_donors')
    
    # merge the donors with the larger dataframe
    merged_covid_ppe_hosp_donors_df = merged_covid_ppe_hosp_df.join(
        donors_df_counties[['fips','ppe_donors']].set_index('fips'),
        on='fips',  how='left', lsuffix='merged', rsuffix='donors')
    
    # fill the NA in counts with 0s
    merged_covid_ppe_hosp_donors_df['ppe_donors'].fillna(0, inplace=True)
    
    # Create text column for use in mapping
    merged_covid_ppe_hosp_donors_df['ppe_donors_requests_text'] = merged_covid_ppe_hosp_donors_df['county'].astype(str) + ', ' + \
        merged_covid_ppe_hosp_donors_df['STATE'].astype(str) + '<br><br>'+\
        'PPE Donors:' + merged_covid_ppe_hosp_donors_df['ppe_donors'].astype(int).astype(str) + '<br>'+ \
        'PPE Requests:' + merged_covid_ppe_hosp_donors_df['PPE_requests'].astype(int).astype(str) + '<br><br>'+ \
        'Covid19: ' + '<br>'+ \
        'Cases: ' + merged_covid_ppe_hosp_donors_df['cases'].astype(int).astype(str) + '<br>'+ \
        'Deaths: ' + merged_covid_ppe_hosp_donors_df['deaths'].astype(int).astype(str) + '<br><br>' + \
        'HAZARD RATIO (Cases/Bed): ' + merged_covid_ppe_hosp_donors_df['Covid_cases_per_bed'].astype(float).astype(str) 

    return merged_covid_ppe_hosp_donors_df

# In order to avoid divide by zero problem in lambda function within calculate_donor_per_requester
def weird_division_for_donor_per_requester(n, d):
    if n ==0:
        return 'NA'
    return n / d if d else 0

def calculate_donor_per_requester(merged_covid_ppe_hosp_donors_df):
    # calculate the covid patients per bed, adding the column that saves this info
    merged_covid_ppe_hosp_donors_df['PPE_Donor_Per_Requester'] = merged_covid_ppe_hosp_donors_df.apply(
            lambda x: (weird_division_for_donor_per_requester(x['ppe_donors'], x['PPE_requests'])), axis=1)
    
    # Create text column for use in mapping
    merged_covid_ppe_hosp_donors_df['ppe_donors_requests_ratio_text'] = merged_covid_ppe_hosp_donors_df['county'].astype(str) + ', ' + \
        merged_covid_ppe_hosp_donors_df['STATE'].astype(str) + '<br><br>'+\
        'GetUsPPE Donors per Requester: ' + merged_covid_ppe_hosp_donors_df['PPE_Donor_Per_Requester'].astype(str) + '<br>'+\
        'PPE Donors: ' + merged_covid_ppe_hosp_donors_df['ppe_donors'].astype(int).astype(str) + '<br>'+ \
        'PPE Requests: ' + merged_covid_ppe_hosp_donors_df['PPE_requests'].astype(int).astype(str) + '<br><br>'+ \
        'Covid19: ' + '<br>'+ \
        'Cases: ' + merged_covid_ppe_hosp_donors_df['cases'].astype(int).astype(str) + '<br>'+ \
        'Deaths: ' + merged_covid_ppe_hosp_donors_df['deaths'].astype(int).astype(str) + '<br><br>' + \
        'HAZARD RATIO (Cases/Bed): ' + merged_covid_ppe_hosp_donors_df['Covid_cases_per_bed'].astype(float).astype(str) 
    
    # TODO
    # Make idempotent, can't be run twice currently
    
    return merged_covid_ppe_hosp_donors_df


# Taking original mask_df from the findthemasks website, rename to current convention
def create_requestor_df_for_querying_requesters(mask_df, merged_covid_ppe_hosp_df):
    requestor_info_df = mask_df.rename(columns={
        'Lat':'lat',
        'Lng':'lon',
        'What is the name of the hospital or clinic?':'institution',
        'Street address for dropoffs?':'address',
        'City':'city',
        "Write drop-off instructions below or paste a link to your organization's own page containing instructions. For written instructions, please include details such as curbside procedure, mailing address, email address, and/or phone number. Please note all information entered here will be made public.": 'instructions',
        'What do you need?' : 'need',
        'fips':'fips'
    })

    ### Merge on the hazard index
    requestor_info_df = pd.merge(requestor_info_df, 
        merged_covid_ppe_hosp_df[['fips','Covid_cases_per_bed']], on='fips', how='left')

    requestor_info_df = requestor_info_df.rename(
        columns={'Covid_cases_per_bed':'Hazard_Index_Covid_Cases_Per_Hosp_Bed'})

    #df = pd.merge(df,df2[['Key_Column','Target_Column']],on='Key_Column', how='left')


    # make sure lat long are float 
    requestor_info_df['lat'] = pd.to_numeric(requestor_info_df['lat'], errors='coerce')
    requestor_info_df['lon'] = pd.to_numeric(requestor_info_df['lon'], errors='coerce')

    # Clean the data by dropping rows that are missing lat lon
    requestor_info_df = requestor_info_df.dropna(how='any', subset=['lat']) 
    requestor_info_df = requestor_info_df.dropna(how='any', subset=['lon']) 
    
    '''EXAMPLE HOW TO USE
    # select lat long from the donors list 
    row = ppe_donors_with_zip_df.loc[ppe_donors_with_zip_df['Name'] == 'Kate Clancy']
    v = {'lat': row['lat'].iloc[0], 'lon': row['lon'].iloc[0]}

    # Pul Top 5 closest donors to location
    k5_closest(
        requestor_info_df[['institution','address','city','instructions','need','lat','lon']].to_dict('records'),
        v)
    '''
    
    return requestor_info_df










