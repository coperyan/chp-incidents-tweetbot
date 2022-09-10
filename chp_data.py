import os
import pandas as pd
import time
import numpy as np
import json
import firebase_admin
from firebase_admin import db
from datetime import timedelta, datetime

from twitter_bot import create_tweet, create_tweet_reply

# Limit for tweets (mins)
LIMIT_MINS = 30

# Setting off data truncation
pd.set_option("display.max_colwidth", None)

chp_centers_dir = "data/chp_communications_centers.csv"
incident_dir = "data/incidents.csv"
incident_activity_dir = "data/incident_activity.csv"

type_exclusions = [
    "Traffic Advisory",
    "SILVER Alert",
    "Assist CT with Maintenance",
    "Road/Weather Conditions",
    "Assist with Construction",
    "ESCORT for Road Conditions",
    "Live or Dead Animal",
    "Wind Advisory",
    "Closure of a Road",
    "Request CalTrans Notify",
]

activity_exclusions = ["Unit Information"]


def time_check(time):
    today_date = datetime.now().date()
    data_time = datetime.combine(today_date, datetime.strptime(time, "%I:%M %p").time())
    now_time = datetime.now()
    min_diff = (now_time - data_time).total_seconds() / 60
    if min_diff <= LIMIT_MINS and min_diff > 0:
        return True
    else:
        return False


def get_type_exclusions():
    return type_exclusions


def get_activity_exclusions():
    return activity_exclusions


def get_firebase():
    with open("creds/database.json", "r") as j:
        contents = json.loads(j.read())
    database_url = contents["databaseURL"]
    cred_obj = firebase_admin.credentials.Certificate("creds/firebase_secret.json")
    default_app = firebase_admin.initialize_app(cred_obj, {"databaseURL": database_url})
    return default_app


def get_chp_centers():
    df = pd.read_csv(chp_centers_dir, header=None)
    return df[0].tolist()


# Get incidents from firebase
def get_firebase_data():
    ref = db.reference("/Incidents")
    query_results = ref.get()
    return query_results


# Add incident to firebase
def upload_incident(incident_dict, new_incident, new_activity):

    # Extracting activity list from dict and removing
    activity_list = incident_dict["activity"]

    # New incident
    if new_incident:
        incident_dict.pop("activity")

        # Setting reference to main incidents
        ref = db.reference("/Incidents")

        # Adding record and naming based on incident ID
        ref.child(incident_dict["incident_id"]).set(incident_dict)

    # Updating activity
    if new_activity:
        # Setting new reference based on incident we just added
        ref = db.reference(
            "/Incidents/{}/activity".format(incident_dict["incident_id"])
        )

        # Looping through activity and adding
        for activity in activity_list:
            ref.child(activity["incident_activity_id"]).set(activity)


# Get list of existing incidents
def get_existing_incidents():
    try:
        all_data = get_firebase_data()
        return list(all_data.keys())
    except:
        return []


# Get list of existing activity
def get_existing_activity():
    try:
        all_data = get_firebase_data()
        activity_list = []
        for key, value in all_data.items():
            iter_activity = all_data[key]["activity"]
            for key in iter_activity.keys():
                activity_list.append(key)
        return activity_list
    except:
        return []


# Get all incidents that haven't been tweeted
def get_untweeted_incidents():

    # Get firebase data
    all_data = get_firebase_data()

    # Create empty list to dump incidents
    all_data_list = []

    # Iterate over incidents
    for key, value in all_data.items():
        # If incident tweet id does not exist
        if all_data[key]["incident_tweet_id"] == 0 and time_check(
            all_data[key]["incident_time"]
        ):
            # Iter Dict
            iter_dict = dict(all_data[key])
            # Remove activity from temp dict
            del iter_dict["activity"]
            # Add to list
            all_data_list.append(iter_dict)

    return all_data_list


# Get all incident activity that hasn't been tweeted
def get_untweeted_activity():
    # Get firebase data
    all_data = get_firebase_data()

    # Create empty list to dump activity dicts
    all_data_list = []

    # Iterate over incidents
    for key, value in all_data.items():
        # Activity of incident
        iter_dict = all_data[key]["activity"]
        # Iterating over activity
        for key1, value1 in iter_dict.items():
            # if not tweeted, incident IS tweeted and passes time check,
            if (
                iter_dict[key1]["activity_tweet_id"] == 0
                and all_data[key]["incident_tweet_id"] != 0
                and time_check(iter_dict[key1]["activity_dt"])
            ):
                # Create dict with activity, no reference
                iter_dict_2 = dict(iter_dict[key1])
                # Adding parent incident tweet
                iter_dict_2["incident_tweet_id"] = all_data[key]["incident_tweet_id"]
                iter_dict_2["incident_id"] = all_data[key]["incident_id"]
                # Appending to list
                all_data_list.append(iter_dict_2)

    # Sorting by activity num so further loops will tweet in order
    all_data_list = sorted(all_data_list, key=lambda k: k["activity_num"])

    return all_data_list


# Updates incident-level tweet IDs
def upload_incident_tweet(incident, tweet_id):
    ref = db.reference("/Incidents/{}".format(incident))
    ref.update({"incident_tweet_id": tweet_id})


# Updates missing activity level tweet IDs
def upload_activity_tweet(incident, activity, tweet_id):
    ref = db.reference("/Incidents/{}/activity/{}".format(incident, activity))
    ref.update({"activity_tweet_id": tweet_id})


# Create new tweets
def create_new_tweets():
    # Test data
    untweeted_incidents = get_untweeted_incidents()
    untweeted_ct = len(untweeted_incidents)
    untweeted_ctr = 0

    for incident in untweeted_incidents:
        untweeted_ctr += 1
        iter_tweet_id = create_tweet(incident)
        iter_incident_id = incident["incident_id"]
        upload_incident_tweet(iter_incident_id, iter_tweet_id)
        time.sleep(1)
        print("Tweeted {} of {} new incidents..".format(untweeted_ctr, untweeted_ct))

    untweeted_activity = get_untweeted_activity()
    untweeted_ct = len(untweeted_activity)
    untweeted_ctr = 0

    for activity in untweeted_activity:
        untweeted_ctr += 1
        iter_tweet_id = create_tweet_reply(activity)
        iter_incident_id = activity["incident_id"]
        iter_activity_id = activity["incident_activity_id"]
        upload_activity_tweet(iter_incident_id, iter_activity_id, iter_tweet_id)
        time.sleep(1)
        print("Tweeted {} of {} new activity..".format(untweeted_ctr, untweeted_ct))


# Initializing firebase
get_firebase()
