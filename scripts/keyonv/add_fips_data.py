import pandas as pd
import json
import requests

url = 'http://findthemasks.com/data.json'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
# Download the data
s = requests.get(url, headers=headers).text
# Extract the JSON format, and find column headers
json_data = json.loads(s)
df = pd.DataFrame.from_dict(json_data['values'][2:])
df.columns = json_data['values'][1]

def get_zipcode(row):
  return row['address'][-5:]

def get_metro_indicator(row):
    return int(row['rucc_2013']) < 3

df['zipcode'] = df.apply(lambda row: get_zipcode(row), axis=1)
rucc_codes = pd.read_csv('data/rucc_codes_2013.csv', 
                         converters={'FIPS': lambda x: str(x)})
rucc_codes.columns = map(str.lower, rucc_codes.columns)
rucc_codes['metro'] = rucc_codes.apply(lambda row: get_metro_indicator(row),
                                       axis=1).astype(int)

# Use crosswalk that matches zipcodes with FIPS codes.
zip_county_crosswalk = pd.read_csv(
    'data/zip_county_crosswalk.csv', converters={'ZIP': lambda x: str(x), 
                                            'COUNTY': lambda x: str(x)})
zip_county_crosswalk.columns = map(str.lower, zip_county_crosswalk.columns)

# Some zipcodes have multiple FIPS codes, so use the FIPS code that has the largest overlap.
idx = (zip_county_crosswalk.groupby(['zip'])['tot_ratio'].transform(max) == 
       zip_county_crosswalk['tot_ratio'])
zip_max_county = zip_county_crosswalk[idx]

# Merge so we have one FIPS (i.e. county) for each zipcode.
zip_metro = zip_max_county[['zip', 'county']].merge(
    rucc_codes[['fips', 'metro']], 
    left_on='county', 
    right_on='fips').drop('county', axis=1)

# Combine main df with metropolitan information
merged_df = df.merge(zip_metro, left_on='zipcode', right_on='zip').drop(
    'zip', axis=1)

merged_df.to_csv('data/requests_fips.csv', index=False)