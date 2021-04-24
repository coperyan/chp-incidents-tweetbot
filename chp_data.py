import os
import pandas as pd
import time 

from twitter_bot import create_tweet

chp_centers_dir = 'data/chp_communications_centers.csv'
incident_dir = 'data/incidents.csv'
incident_activity_dir = 'data/incident_activity.csv'

type_exclusions = [
    'Traffic Advisory',
    'SILVER Alert',
    'Assist CT with Maintenance',
    'Road/Weather Conditions',
    'Assist with Construction',
    'ESCORT for Road Conditions',
    'Live or Dead Animal',
    'Wind Advisory',
    'Closure of a Road',
    'Request CalTrans Notify'
]

activity_exclusions = [
    'Unit Information'
]

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
    df = get_incident_df()
    df = df[df['incident_tweet_id'].isna()]
    df = df[df['incident_type'].isin(type_exclusions) == False]  
    return df

#Get all incident activity that hasn't been tweeted
def get_untweeted_activity():
    df = get_incident_df()
    df2 = get_incident_activity_df()
    
    #Get rid of all tweeted activity
    df2 = df2[df2['activity_tweet_id'].isna()]

    #Exclude activity types 
    df2 = df2[df2['activity_type'].isin(activity_exclusions) == False]
    
    #Getting tweeted incidents
    tweeted_incidents = df[df['incident_tweet_id'].notnull()][['incident_id','incident_tweet_id']]
    
    #Merging tweeted incidents to populate the incident tweet ID
    df2 = df2.merge(tweeted_incidents,how='inner',on='incident_id')
    df2 = df2.drop(columns=['incident_tweet_id_x'])
    df2.rename(columns={'incident_tweet_id_y':'incident_tweet_id'},inplace=True)

    #Resorting by incident_id, activity_num
    df2 = df2.sort_values(by=['incident_id','activity_num'],ascending=[True,True])

    return df2

    

#Function to create new tweets about incidents

#Function to create new replies providing updates on incidents

#Get initial DFs
incident_df = get_incident_df()
incident_activity_df = get_incident_activity_df()

#Get untweeted incidents
untweeted_incidents = get_untweeted_incidents()
untweeted_ct = len(untweeted_incidents)
untweeted_ctr = 0 

#Iterate over untweeted incidents
#Create tweet
#Store ID in incident df
for index, row in untweeted_incidents.iterrows():
    untweeted_ctr += 1
    iter_dict = untweeted_incidents.loc[index].to_dict()
    iter_id = create_tweet(iter_dict)
    iter_incident_id = row['incident_id']
    incident_df.loc[incident_df.incident_id == iter_incident_id, 'incident_tweet_id'] = iter_id
    time.sleep(1)
    print('Tweeted {} of {} new incidents..'.format(untweeted_ctr,untweeted_ct))
    if untweeted_ctr >= 10:
        break

#Save incident df progress
save_incident_df(incident_df)

#Get all untweeted activity
untweeted_activity = get_untweeted_activity()
untweeted_ct = len(untweeted_activity)
untweeted_ctr = 0

