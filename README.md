# Getting started
Visit [GetUsPPE](https://getusppe.org/) and [findthemasks](https://findthemasks.com/give.html). 
**Installing python environment**
```bash
conda create --name getusppe python=3.7
source activate getusppe
pip install -r requirements.txt
```

## Projects
- Hospital Status and PPE Needs: Jennifer (Current mock)
![Alt text](img/Hospital_Status_and_PPE_Needs.png?raw=true "Hospital_Status_and PPE_Needs.png")
<p align="left">
    <b></b><br>
</p>

- Heat maps of PPE requests: Brian and Ian
![Alt text](img/Heat_Maps_of_PPE_requests.png?raw=true "Heat_Maps_of_PPE_requests.png")

- Colocalization of COVID19 Cases and PPE Requests: Matt, Nick and Keyon
![Alt text](img/Colocalization_of_COVID19_Cases_and_PPE_Requests.png?raw=true "Colocalization_of_COVID19_Cases_and_PPE_Requests.png")

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