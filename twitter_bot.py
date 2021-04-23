import twitter
import json

from chp_data import get_incident_df

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

def get_incident_format(incident):
    incident_text = """%s - %s - %s -%s"""
    % (incident['chp_center'],
    % (incident['incident_area'])
    incident['incident_type'],
    incident['incident_location'])

    # MAY NEED TO ADD SPLIT FOR CHARACTER LIMITS

def get_activity_format(activity):
    return None


#def create_tweet(incident):

incident_df = get_incident_df()
test_dict = incident_df.loc[0].to_dict()
api = get_twitter_api()
status = api.PostUpdate()
    


#function to add replies to existing incident tweet

#function to create new master tweet for an incident

