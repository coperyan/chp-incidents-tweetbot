import os
import pandas as pd
import time
import numpy as np
import json
import firebase_admin
from firebase_admin import db
from datetime import timedelta, datetime

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

def get_data_age(time):
    today_date = datetime.now().date()
    data_time = datetime.combine(today_date,datetime.strptime(time,'%I:%M %p').time())
    now_time = datetime.now()
    return (now_time - data_time) / 60

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

#Get incidents from firebase
def get_firebase_data():
    ref = db.reference('/Incidents')
    query_results = ref.get()
    return query_results

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

#Get all incidents that haven't been tweeted
def get_untweeted_incidents():
    #Get firebase data
    all_data = get_firebase_data()

    #Create empty list to dump incidents
    all_data_list = []

    #Iterate over incidents
    for key, value in all_data.items():
        #If incident tweet id does not exist 
        if all_data[key]['incident_tweet_id'] == 0:
            #Remove activity from return
            iter_dict = dict(all_data[key]).pop('activity')
            #Add to list 
            all_data_list.append(iter_dict)
    return all_data_list

#Get all incident activity that hasn't been tweeted
def get_untweeted_activity():
    #Get firebase data
    all_data = get_firebase_data()

    #Create empty list to dump activity dicts
    all_data_list = []

    #Iterate over incidents
    for key, value in all_data.items():
        #Activity of incident 
        iter_dict = all_data[key]['activity']
        #Iterating over activity
        for key1, value1 in iter_dict.items():
            #If activity tweet id does not exist and incident tweet id does exist
            if iter_dict[key1]['activity_tweet_id'] == 0 and all_data[key]['incident_tweet_id'] != 0:
                #Create dict with activity, no reference
                iter_dict_2 = dict(iter_dict[key1])
                #Adding parent incident tweet
                iter_dict_2['incident_tweet_id'] = all_data[key]['incident_tweet_id']
                #Appending to list
                all_data_list.append(iter_dict_2)

    return all_data_list

#Updates incident-level tweet IDs    
def upload_incident_tweet(incident,tweet_id):
    ref = db.reference('/Incidents/{}'.format(incident))
    ref.update({'incident_tweet_id':tweet_id})

#Updates missing activity level tweet IDs
def upload_activity_tweet(incident,activity,tweet_id):
    ref = db.reference('/Incidents/{}/activity/{}'.format(incident,activity))
    ref.update({'activity_tweet_id':tweet_id})

    
def create_new_tweets():

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

#Initializing firebase
get_firebase()

