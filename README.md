# Getting started: [GetUsPPE](https://getusppe.org/) 

## [Examples](https://getusppe.org/data)
- [PPE Requests per county](https://getusppe.github.io/PPE_Requests_Per_County/)
- [Hospital beds per county](https://getusppe.github.io/Hospital_bed_per_county/)
- [Covid19 cases per county](https://getusppe.github.io/Covid19_Cases_Per_County/)
- [Hazard Ratio](https://getusppe.github.io/Hazard_Ratio_Possible_PPE_Need_Covid19/)

## Repo Format 
- **src**: Python classes and functions for data downloading, processing and mapping
- **notebooks**: Example code from repo contributors
- **scripts**: TODO: Move into src folder

## Installing python environment
```bash
conda create --name getusppe python=3.7
conda activate getusppe
pip install -r requirements.txt
```

## Using the package
##### Sample code to pull live findthemasks data into pandas
```python
import json, requests
import pandas as pd
# Specify URL and also headers (findthemasks requires browser headers)
url = 'http://findthemasks.com/data.json'
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"}
# Download the data
s=requests.get(url, headers= headers).text
# Extract the json format, and find column headers
json_data = json.loads(s)
HEADERS = json_data['values'][0]
print(HEADERS)
# create the data frame
mask_df = pd.DataFrame.from_dict(json_data['values'][2:])
mask_df.columns=HEADERS
```