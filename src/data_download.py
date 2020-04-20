import requests
import pandas as pd
import json
import time
import addfips

def download_findthemasks_data(url,request_headers, write_out_csv=False):
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

    # Rename long column header: drop off instructions
    mask_df.rename(columns={'Drop off instructions, eg curbside procedure or mailing address. If you want donors to email or call you, please include contact info that can be made public in this field:': 'Drop_Off_Instructions'}, inplace=True)

    # Download a local copy of the find the masks json object
    if write_out_csv == True:
        timestr = time.strftime("%Y%m%d")
        path = 'find_the_mask_json_' + timestr + '.csv'
        mask_df.to_csv (path, index = False, header=True)
    
    return mask_df


def download_nytimes_data(url, date, write_out_csv = True):
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

def remove_negative_values_replace_with_zero(n):
    if n < 0:
        return 0
    return n

def download_hospital_data(url, write_out_csv = True):
    hospital_df = pd.read_csv(url)

    # TODO: Move this processing code probably into data processing class
    
    # TODO: Leverage geocoder class instead of this code
    af = addfips.AddFIPS()

    # Reverse geocoder used to get geocoded fips and county information
    # Note: Progress_apply is used for the timer functionality
    hospital_df['fips'] = hospital_df.apply(
        lambda x: (af.get_county_fips(x['COUNTY'], x['STATE'])), axis=1)
    
    # clean the BEDS column to make sure all are positive in value, by converting negative beds to 0
    hospital_df['BEDS'] = hospital_df.apply(
        lambda x: (remove_negative_values_replace_with_zero(x['BEDS'])), axis=1 )

    # write out this data file to csv
    if write_out_csv:
        timestr = time.strftime("%Y%m%d")
        path = 'hospital_data_processed_' + timestr + '.csv'
        hospital_df.to_csv (path, index = False, header=True)

    return hospital_df


def download_PPE_donors(url='https://docs.google.com/spreadsheet/ccc?key=1sW5jAik3olWGWtIC_i3khBEO6Hltj5SfzyM9mDoTeUc&output=csv'):
    ppe_donors_df = pd.read_csv(url)
    
    # Rename the column
    ppe_donors_df.rename(inplace=True, columns={
        'Institution or Affiliation': 'Affiliation',
        'Zip Code':'zip'
    })
    
    # Zfill all countyFIPS to be 5 characters
    width=5
    ppe_donors_df["zip"]= ppe_donors_df["zip"].astype(str)
    ppe_donors_df["zip"]= ppe_donors_df["zip"].str.zfill(width) 
    
    # Clean the data by dropping rows that are missing name, instituion, zip code
    ppe_donors_df = ppe_donors_df.dropna(how='any', subset=['zip', 'Name'])
    
    # Make the zip column a string
    ppe_donors_df['zip']=ppe_donors_df['zip'].astype(str)
    
    # Clean the data by dropping columns that are not needed
    ppe_donors_df.drop(['State'],axis=1, inplace=True)
    
    return ppe_donors_df


def download_zip_to_fips_data(url='https://docs.google.com/spreadsheet/ccc?key=1XivjeJ-NaTiVJYhEXYoCONI_6aZHlKAp5v3qUb6gZd4&output=csv'):
    zip_fips_df = pd.read_csv(url)
    
    # remove the word county from all counties
    zip_fips_df["county"] = zip_fips_df["county"].str.replace(" County", "")
    
    # map the zip to a string to join later
    zip_fips_df['zip']=zip_fips_df['zip'].astype(str)
    
    # Clean the data by dropping columns that are not needed
    zip_fips_df.drop(['classfp'],axis=1, inplace=True)
    
    return zip_fips_df

def download_ideo_merged_data(url, zip_fips_df, write_out_csv = True):
    ideo_df = pd.read_csv(url)
    
    # zfill the fips to make sure they are right
    width=5
    zip_fips_df["fips"]= zip_fips_df["fips"].astype(str)
    zip_fips_df["fips"]= zip_fips_df["fips"].str.zfill(width) 
    zip_fips_df["zip"]= zip_fips_df["zip"].astype(str)
    zip_fips_df["zip"]= zip_fips_df["zip"].str.zfill(width) 
    ideo_df["zip"]= ideo_df["zip"].astype(str)
    ideo_df["zip"]= ideo_df["zip"].str.zfill(width) 
    
    # join the ppe_donors with the zip code to add fips, state, county info
    ideo_df = ideo_df.join(zip_fips_df.set_index('zip'),
             how='left',on='zip', lsuffix='donors', rsuffix='zip')
    
    # Clean the data by dropping rows that are missing fips
    ideo_df = ideo_df.dropna(how='any', subset=['fips'])  
    
    ideo_df.rename(inplace=True, columns={
        'statezip': 'State', })
    
    # write out this data file to csv
    if write_out_csv:
        timestr = time.strftime("%Y%m%d")
        path = 'ideo_data_processed_' + timestr + '.csv'
        ideo_df.to_csv (path, index = False, header=True)

    return ideo_df

