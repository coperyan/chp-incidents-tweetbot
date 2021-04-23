import twitter
import json

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

api = get_twitter_api()
    


#function to add replies to existing incident tweet

#function to create new master tweet for an incident

