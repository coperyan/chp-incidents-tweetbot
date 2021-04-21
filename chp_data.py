import os
import pandas as pd

chp_centers_dir = 'data/chp_communications_centers.csv'

col_list = [
    'chp_center',
    'incident_number',
    'incident_type',
    'incident_location',
    'incident_location_description',
    'incident_lat',
    'incident_lng',
    'activity_type',
    'activity_dt',
    'activity_num',
    'activity_text'
]

def get_chp_centers():
    df = pd.read_csv(chp_centers_dir,header=None)
    return df[0].tolist()

def get_incident_df():
    df = pd.DataFrame(columns=col_list)
    return df