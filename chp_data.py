import os
import pandas as pd

chp_centers_dir = 'data/chp_communications_centers.csv'
incident_dir = 'data/incidents.csv'
incident_activity_dir = 'data/incident_activity.csv'

def get_chp_centers():
    df = pd.read_csv(chp_centers_dir,header=None)
    return df[0].tolist()

def get_incident_df():
    df = pd.read_csv(incident_dir)
    return df

def save_incident_df(df):
    df.to_csv(incident_dir,index=None)

def get_incident_activity_df():
    df = pd.read_csv(incident_activity_dir)
    return df

def save_incident_activity_df(df):
    df.to_csv(incident_activity_dir,index=None)

#Updates missing incident-level tweet IDs    
def refresh_incident_tweet_ids():
    df = get_incident_df()

    #Getting existing tweet IDs
    df_ids = df[df['incident_tweet_id'].notnull()][['incident_number','incident_tweet_id']]

    #Using map function to apply val across all records for incident number
    df['incident_tweet_id'] = df['incident_number'].map(df_ids.set_index('incident_number')['incident_tweet_id'])

    save_incident_df(df)

#Get all incidents that haven't been tweeted
def get_untweeted_incidents():
    return None

#Function to create new tweets about incidents

#Function to create new replies providing updates on incidents

incident_df = get_incident_df()
incident_activity_df = get_incident_activity_df()