import os
import pandas as pd
import time
import numpy as np
import json
import firebase_admin
from firebase_admin import db

from twitter_bot import create_tweet, create_tweet_reply

#Setting off data truncation
pd.set_option('display.max_colwidth', None)

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

def get_type_exclusions():
    return type_exclusions

def get_activity_exclusions():
    return activity_exclusions

def get_firebase():
    with open('creds/database.json', 'r') as j:
        contents = json.loads(j.read())
    database_url = contents['databaseURL']
    cred_obj = firebase_admin.credentials.Certificate('creds/firebase_secret.json')
    default_app = firebase_admin.initialize_app(cred_obj, {'databaseURL':database_url})
    return default_app

def get_chp_centers():
    df = pd.read_csv(chp_centers_dir,header=None)
    return df[0].tolist()

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
    df = df[df['incident_tweet_id'] == 0]
    df = df[df['incident_type'].isin(type_exclusions) == False]  
    return df

#Get all incident activity that hasn't been tweeted
def get_untweeted_activity():
    df = get_incident_df()
    df2 = get_incident_activity_df()
    
    #Get rid of all tweeted activity
    df2 = df2[df2['activity_tweet_id'] == 0]

    #Exclude activity types 
    df2 = df2[df2['activity_type'].isin(activity_exclusions) == False]
    
    #Getting tweeted incidents
    tweeted_incidents = df[df['incident_tweet_id'] != 0][['incident_id','incident_tweet_id']]
    
    #Merging tweeted incidents to populate the incident tweet ID
    df2 = df2.merge(tweeted_incidents,how='inner',on='incident_id')
    df2 = df2.drop(columns=['incident_tweet_id_x'])
    df2.rename(columns={'incident_tweet_id_y':'incident_tweet_id'},inplace=True)

    #Resorting by incident_id, activity_num
    df2 = df2.sort_values(by=['incident_id','activity_num'],ascending=[True,True])

    return df2

    
def create_new_tweets():
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

    #Iterate over untweeted activity
    #Create tweet
    #Store ID in activity DF
    for index, row in untweeted_activity.iterrows():
        untweeted_ctr += 1
        iter_dict = untweeted_activity.loc[index].to_dict()
        iter_id = create_tweet_reply(iter_dict)
        iter_activity_id = row['incident_activity_id']
        incident_activity_df.loc[incident_activity_df.incident_activity_id == iter_activity_id,'activity_tweet_id'] = iter_id
        time.sleep(1)
        print('Tweeted {} of {} new activity..'.format(untweeted_ctr,untweeted_ct))
        if untweeted_ctr >= 10:
            break  

    #Save incident activity df progress
    save_incident_activity_df(incident_activity_df)

#Add incident to firebase
def upload_incident(incident_dict,new_incident,new_activity):

    #Extracting activity list from dict and removing
    activity_list = incident_dict['activity']

    #New incident
    if new_incident:
        incident_dict.pop('activity')

        #Setting reference to main incidents
        ref = db.reference('/Incidents')

        #Adding record and naming based on incident ID
        ref.child(incident_dict['incident_id']).set(incident_dict)

    #Updating activity
    if new_activity:
        #Setting new reference based on incident we just added 
        ref = db.reference('/Incidents/{}/activity'.format(incident_dict['incident_id']))
        
        #Looping through activity and adding
        for activity in activity_list:
            ref.child(activity['incident_activity_id']).set(activity)

#Get incidents from firebase
def get_firebase_data():
    ref = db.reference('/Incidents')
    query_results = ref.get()
    return query_results

#Get list of existing incidents
def get_existing_incidents():
    all_data = get_firebase_data()
    return list(all_data.keys())
    
#Get list of existing activity
def get_existing_activity():
    all_data = get_firebase_data()
    activity_list = []
    for key, value in all_data.items():
        iter_activity = all_data[key]['activity']
        for key in iter_activity.keys():
            activity_list.append(key)
    return activity_list

#Initializing firebase
get_firebase()

## Need to create JSON from dataframes
## First dict will have the entire incident-level info from there
## One of the dict keys will be activity, and within activity there will be a list of activity dicts
## Can import manually from there


# incident_df = get_incident_df()
# incident_activity_df = get_incident_activity_df()
# data_dict_list = []

# for index, row in incident_df.iterrows():
#     iter_activity_list = []
#     iter_dict = row.to_dict()
#     iter_activity_df = incident_activity_df[incident_activity_df.incident_id == row['incident_id']]
#     for index1, row1 in iter_activity_df.iterrows():
#         iter_activity_list.append(row1.to_dict())
#     iter_dict['activity'] = iter_activity_list
#     data_dict_list.append(iter_dict)

# test = {}
# test['Incidents'] = data_dict_list

# output_file = 'data/data.json'
# with open(output_file,'w') as f:
#     json.dump(test,f)


# dict_list = []
# incident_dict = incident_df[incident_df.incident_id=='Ventura_00139'].iloc[0].to_dict()
# incident_dict['activity'] = []
# incident_activity = incident_activity_df[incident_activity_df.incident_id == 'Ventura_00139']
# for index, row in incident_activity.iterrows():
#     dict_list.append(row.to_dict())

# incident_dict['activity'] = dict_list

# ref = db.reference('/')
# ref.set({'Incidents':{}})
# ref = db.reference('/Incidents')
# for key, value in incident_dict.items():
#     if type(value) == np.int64:
#         print(value)

# incident_dict['incident_number'] = int(incident_dict['incident_number'])
# incident_dict['incident_tweet_id'] = int(incident_dict['incident_tweet_id'])
 
# ref.child(incident_dict['incident_id']).set(incident_dict)
