# Getting started: [GetUsPPE](https://getusppe.org/) 

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

## Data Acess
- **Open Access Data**: GetUsPPE.org is partnered with [#findthemasks](https://findthemasks.com/give.html). To use this data (3000+ PPE Requests), go to src/config.ini, and change the find_the_masks_data_download_flag to True:
```
find_the_masks_data_download_flag = True
```
- **Request-Only Access Data**: GetUsPPE.org has an additional dataset that compromises quantitative demand side information (i.e. Nursing Home X requests 20 Face Shields, with less than 2 days supppy remaining). To use this dataset, [please reach out to GetUsPPE.org for access](https://docs.google.com/forms/d/e/1FAIpQLSeuTWRkBvPHBPor0bk9entuIKa6W0oCuVnz2-VI_hn_i3hmVQ/viewform?usp=sf_link), Then change:
```
find_the_masks_data_download_flag = False
```

## Sample code to create the figures
Navigate to getusppe_viz/src
```python
python create_figures.py
```
- Interested in exploring all of the data, [checkout this notebook](https://github.com/GetUsPPE/getusppe_viz/blob/master/notebooks/mattr/Correlation_PPE_Demand_With_Covid19_Cases_v2.ipynb)
- Interested in exploring the quantitative supply side data (this requires data to be requested), [checkout this notebook](https://github.com/GetUsPPE/getusppe_viz/blob/master/notebooks/mattr/New%20Survey%20Analysis%20-%20MattR%20Edits.ipynb)