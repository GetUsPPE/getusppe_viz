import geopandas as gpd
import reverse_geocoder as rg
import addfips
import requests
import pandas as pd

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
            return {'fips':'NA', 'county':'NA'}  # dropna() may not drop 'NA'

    def get_geocoder_info_from_rg_vector(self, Lats, Lngs):
        """Returns a column of the form [{'fips': fips, 'county': county}]"""
        # Reverse geocoder api call to get county names
        results = rg.search(list(zip(Lats, Lngs))) # default mode = 2
        fips_not_found_count = 0
        fips_info_list = []
        for res in results:
            county = res['admin2']
            state = res['admin1']

            try:
                # Lookup of fips code (https://github.com/fitnr/addfips)
                current_fips = self.fips_code_lookup(county, state)

                # add the fip and county
                fips_info_list.append({'fips':current_fips, 'county':county})
            except ValueError:
                fips_not_found_count += 1
                fips_info_list.append({'fips':'NA', 'county':'NA'})
        if fips_not_found_count:
            print('{} fips were not found.'.format(fips_not_found_count))
        return fips_info_list
