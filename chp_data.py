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

#Updates missing incident-level tweet IDs    
def refresh_incident_tweet_ids():
    df = get_incident_df()

    #Getting existing tweet IDs
    df_ids = df[df['incident_tweet_id'].notnull()][['incident_number','incident_tweet_id']]

    #Using map function to apply val across all records for incident number
    df['incident_tweet_id'] = df['incident_number'].map(df_ids.set_index('incident_number')['incident_tweet_id'])

    save_incident_df(df)


#Function to create new tweets about incidents

#Function to create new replies providing updates on incidents
