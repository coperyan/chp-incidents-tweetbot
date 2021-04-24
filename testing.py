import pandas as pd
import os
import twitter
import json

from chp_data import get_incident_df, save_incident_df
from chp_data import get_incident_activity_df, save_incident_activity_df

def get_creds():
    with open('creds.json', 'r') as j:
        contents = json.loads(j.read())
    return contents

def get_twitter_api():
    creds = get_creds()
    api = twitter.Api(consumer_key = creds['twitterApiKey'],
                    consumer_secret = creds['twitterApiSecret'],
                    access_token_key = creds['twitterAccessToken'],
                    access_token_secret = creds['twitterAccessSecret'])
    return api

def clear_tweet_ids():
    incident_df = get_incident_df()
    incident_df['incident_tweet_id'] = 0
    incident_activity_df = get_incident_activity_df()
    incident_activity_df['activity_tweet_id'] = 0
    save_incident_df(incident_df)
    save_incident_activity_df(incident_activity_df)

def delete_all_tweets():
    more_tweets = True
    while more_tweets:
        api = get_twitter_api()
        tweets = api.GetUserTimeline('1384728473319579649') 
        if len(tweets) == 0:
            more_tweets = False
        for tweet in tweets:
            id_str = tweet._json['id_str']
            api.DestroyStatus(id_str)

delete_all_tweets()
clear_tweet_ids()