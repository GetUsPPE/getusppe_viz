# Getting started: Visit [GetUsPPE](https://getusppe.org/) 
**Installing python environment**
```bash
conda create --name getusppe python=3.7
conda activate getusppe
pip install -r requirements.txt
```

## Examples
- [PPE Requests per county](https://getusppe.github.io/PPE_Requests_Per_County/)
- [Hospital beds per county](https://getusppe.github.io/Hospital_bed_per_county/)
- [Covid19 cases per county](https://getusppe.github.io/Covid19_Cases_Per_County/)
- [Hazard Ratio](https://getusppe.github.io/Hazard_Ratio_Possible_PPE_Need_Covid19/)

## Data Snapshots
Note: These are not kept up to date, but can be used as a reference or testing
- [findthemasks_data_processed_20200328](https://drive.google.com/file/d/1xLrkYf1D63bjDsuptIlC1y1A6z1VN-U7/view?usp=sharing)
- [COVID19_nytimes_2020-03-26 data_processed_on_20200328](https://drive.google.com/file/d/16cNiraOfi1JYVCOI1ovhpmm8M7fsT2O_/view?usp=sharing)
- [hospital_data_processed_per_county20200328](https://drive.google.com/file/d/1XRSjdSbtn3za-ISX_aEJ1DKC0DAUAK89/view?usp=sharing)

## Using the package
#### Sample code to pull live findthemasks data into pandas
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