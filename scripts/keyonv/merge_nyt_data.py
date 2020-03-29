import pandas as pd
import numpy as np

cases = pd.read_csv('data/us-counties.csv', 
                    converters={'fips': lambda x: str(x)})
# NYC data is missing county, so make them all New York County.
cases.loc[cases['county'] == 'New York City', 'fips'] = '36061'
# Kansas City data is missing the specific county so make them all Cook County
cases.loc[(cases['county'] == 'Kansas City') & 
          (cases['state'] == 'Missouri'), 'fips'] = '29095'
# For now, drop all cases with unknown counties.
cases = cases[cases.county != 'Unknown']

# Get new daily cases/deaths for each county from number of cumulative cases.
all_fips = np.unique(cases['fips'])
for fips in all_fips:
    cases.loc[cases['fips'] == fips, 'new_cases'] = np.diff(
            np.insert(np.array(cases[cases['fips'] == fips]['cases']), 0, 0))
    cases.loc[cases['fips'] == fips, 'new_deaths'] = np.diff(
            np.insert(np.array(cases[cases['fips'] == fips]['deaths']), 0, 0))

cases['new_cases'] = cases['new_cases'].astype(int)
cases['new_deaths'] = cases['new_deaths'].astype(int)

demand = pd.read_csv('data/requests_fips.csv', 
                     converters={'fips': lambda x: str(x)})
demand['date'] = pd.to_datetime(demand['timestamp']).dt.date
cases['date'] = pd.to_datetime(cases['date']).dt.date

# Drop duplicates by only including the most recent timestamp for shared names 
# and dates.
duplicates = demand.groupby(['name', 'date', 'state']).timestamp.transform(max)
demand = demand.loc[demand.timestamp == duplicates]

# requests_per_date aggregates the number of requests for each FIPS on any
# given date.
requests_per_date = demand[['fips', 'date', 'accepting']].groupby(
    ['fips', 'date']).count()
# df contains: date, county, number of cases/deaths (new and aggregate), and
# number of institutions asking for supplies.
df = pd.merge(requests_per_date, cases, 
              how='outer',
              left_on=['fips', 'date'], 
              right_on = ['fips', 'date'])

# Assume that values in the requests dataset that weren't listed in the NYT 
# dataset had no new cases/deaths.
df['new_cases'] = df['new_cases'].fillna(0)
df['new_deaths'] = df['new_deaths'].fillna(0)
# Assume that values in the cases dataset that weren't in the requests dataset 
# had no new requests.
df['accepting'] = df['accepting'].fillna(0)

# For now, drop NA's.
df = df.dropna()

# Now we can use df to see how the number of cases and requests vary by 
# county by day. If we want to aggregate over all days, we can do that too.
df_all_days = df[
    ['fips', 'accepting', 'new_cases', 'new_deaths']].groupby(
        'fips', as_index=False).sum()
fips = np.array(df_all_days['fips'])
all_cases = np.array(df_all_days['new_cases'])
all_deaths = np.array(df_all_days['new_cases'])
requests = np.array(df_all_days['accepting'])

# We filter the counties that have not made any requests, and sort by number
# of cases.
most_in_need_fips = fips[np.where(requests == 0)[0]][
    np.argsort(-all_cases[np.where(requests == 0)[0]])]

# Print counties in most need.
for fips in most_in_need_fips[:10]:
    num_cases = int(df_all_days[df_all_days['fips'] == fips]['new_cases'])
    num_requests = int(df_all_days[df_all_days['fips'] == fips]['accepting'])
    county = str(cases[cases['fips'] == fips]['county'].max())
    state = str(cases[cases['fips'] == fips]['state'].max())
    print('{}, {} has {} cases (and {} requests).'.format(
        county, state, num_cases, num_requests))