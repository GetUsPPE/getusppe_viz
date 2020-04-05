from math import cos, asin, sqrt

# Math for determing closest distance
def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
    return 12742 * asin(sqrt(a))

def closest(data, v):
    return min(data, key=lambda p: distance(v['lat'],v['lon'],p['lat'],p['lon']))

def k5_closest(data,v):
    return sorted(data, key=lambda p: distance(v['lat'],v['lon'],p['lat'],p['lon']))[:5]

def k10_closest(data,v):
    return sorted(data, key=lambda p: distance(v['lat'],v['lon'],p['lat'],p['lon']))[:10]

# EXAMPLE HOW TO USE 
''' 
tempDataList = [{'name':'1','lat': 39.7612992, 'lon': -86.1519681}, 
                {'name':'2','lat': 39.762241,  'lon': -86.158436 },
                {'name':'3','lat': 39.862241,  'lon': -86.158436 }, 
                {'name':'4','lat': 39.962241,  'lon': -86.158436 },
                {'name':'5','lat': 39.162241,  'lon': -86.158436 }, 
                {'name':'6','lat': 39.7622292, 'lon': -86.1578917}]

v = {'lat': 50.7622290, 'lon': -121.1519750}

#Example converting list of dict to dataframe
temp_df=pd.DataFrame(tempDataList)

# Example converting dataframe to list of dict
temp_array = temp_df[['name','lat','lon']].to_dict('records')
print(k5_closest(temp_array, v))

# Example for pulling Top 5 closest donors to location
k5_closest(
    ppe_donors_with_zip_df[['Name','lat','lon','state']].to_dict('records'),
    v)
'''
