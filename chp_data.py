import os
import pandas as pd

chp_centers_dir = 'data/chp_communications_centers.csv'
incidents_dir = 'data/incident_data.csv'

def get_chp_centers():
    df = pd.read_csv(chp_centers_dir,header=None)
    return df[0].tolist()

def get_incident_df():
    df = pd.read_csv(incidents_dir)
    return df

def save_incident_df(df):
    df.to_csv(incidents_dir,index=None)
    

#Function to receive DF from scrape, save unique incidents??

#Function to create new tweets about incidents

#Function to create new replies providing updates on incidents


