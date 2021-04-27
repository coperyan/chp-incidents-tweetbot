import twitter
import json

#Get twitter creds
def get_creds():
    with open('creds/creds.json', 'r') as j:
        contents = json.loads(j.read())
    return contents

#Get twitter API object
def get_twitter_api():
    creds = get_creds()
    api = twitter.Api(consumer_key = creds['twitterApiKey'],
                    consumer_secret = creds['twitterApiSecret'],
                    access_token_key = creds['twitterAccessToken'],
                    access_token_secret = creds['twitterAccessSecret'])
    return api

#Get text format for incident
def get_incident_format(incident):
    tweet_text = ''
    if len(incident['incident_time']) > 0:
        tweet_text = '{}[{}]\n'.format(tweet_text,incident['incident_time'])
    tweet_text = '{}{}\n'.format(tweet_text,incident['incident_type'])
    if len(incident['incident_location']) > 0:
        tweet_text = '{}{}\n'.format(tweet_text,incident['incident_location'])
    if len(incident['incident_location_description']) > 0 and incident['incident_location_description'].lower() != incident['incident_location'].lower():
        tweet_text = '{}{}\n'.format(tweet_text,incident['incident_location_description'])
    if len(incident['incident_area']) > 0 and incident['incident_area'] != incident['chp_center']:
        tweet_text = '{}{}'.format(tweet_text,incident['incident_area'])
    #tweet_text = '{}{} CHP'.format(tweet_text,incident['chp_center'])
    tweet_text = '{}\n\n#CHP #CHP{}'.format(tweet_text,incident['chp_center'].replace(' ',''))
    if len(incident['incident_area']) > 0 and incident['incident_area'] != incident['chp_center']:
        tweet_text='{} #{}'.format(tweet_text,incident['incident_area'].replace(' ',''))
    return tweet_text
   
#Get text format for activity
def get_activity_format(activity):
    tweet_text = ''
    if len(activity['activity_dt']) > 0:
        tweet_text = '{}[{}]\n'.format(tweet_text,activity['activity_dt'])
    tweet_text = '{}{}'.format(tweet_text,activity['activity_text'])
    return tweet_text

#Function to create tweet with incident dict
def create_tweet(incident):
    tweet_text = get_incident_format(incident)
    api = get_twitter_api()
    status = api.PostUpdate(tweet_text)
    return int(status._json['id'])

#Function to create tweet with activity dict
def create_tweet_reply(activity):
    tweet_text = get_activity_format(activity)
    incident_tweet_id = int(activity['incident_tweet_id'])
    api = get_twitter_api()
    status = api.PostUpdate(tweet_text,in_reply_to_status_id=incident_tweet_id)
    return int(status._json['id'])
