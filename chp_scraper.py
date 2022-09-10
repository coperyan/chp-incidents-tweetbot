import requests
import os
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
import time

from chp_data import get_chp_centers, upload_incident
from chp_data import get_activity_exclusions, get_type_exclusions
from chp_data import get_existing_activity, get_existing_incidents

driver_path = "/Users/rcope/Downloads/chromedriver"
incidents_url = "https://cad.chp.ca.gov/Traffic.aspx"

ignored_exceptions = (
    NoSuchElementException,
    StaleElementReferenceException,
)

# Function to get incidents
# Update dataframes with NEW incidents or activity
# def get_incidents():
chp_centers = get_chp_centers()
chp_centers = ["Golden Gate"]

activity_exclusions = get_activity_exclusions()
type_exclusions = get_type_exclusions()

existing_activity = get_existing_activity()
existing_incidents = get_existing_incidents()

driver = webdriver.Chrome(executable_path=driver_path)
driver.get(incidents_url)

# Disable auto refresh on page (this may not work)
auto_refresh = driver.find_element_by_id("chkAutoRefresh")
auto_refresh.click()

# Find incidents for each CHP center
for center in chp_centers:
    print("Getting incidents for center {}".format(center))

    # Select center
    center_dd = Select(driver.find_element_by_id("ddlComCenter"))
    center_dd.select_by_visible_text(center)

    # Find incidents (if none, continue loop)
    try:
        incidents_table = driver.find_element_by_id("gvIncidents")
        incidents_rows = incidents_table.find_elements_by_tag_name("tr")
    except:
        continue

    # Remove header BS
    incidents_rows = incidents_rows[1:]

    # Have to create list of incident numbers instead of element reference
    incidents_list = []
    for row in incidents_rows:
        incidents_list.append(row.find_elements_by_tag_name("td")[1].text)
    incident_ct = len(incidents_list)
    print("{} incident(s) found for center {}".format(incident_ct, center))

    # New incident, activity counters for center
    new_incident_ctr = 0
    new_activity_ctr = 0

    # Get details for each incident
    for incident in incidents_list:

        # Need to rediscover element based on matching incident ID
        incidents_table = driver.find_element_by_id("gvIncidents")
        incidents_rows = incidents_table.find_elements_by_tag_name("tr")
        incidents_rows = incidents_rows[1:]
        for row in incidents_rows:
            if row.find_elements_by_tag_name("td")[1].text == incident:
                incident_row = row
                break

        # Click detail href and expand details - sometimes this fails and we need to try twice
        try:
            detail_href = incident_row.find_element_by_tag_name("a")
            detail_href.click()
            incident_data = driver.find_element_by_id("pnlDetails")
        except:
            try:
                time.sleep(10)
                detail_href = incident_row.find_element_by_tag_name("a")
                detail_href.click()
                incident_data = driver.find_element_by_id("pnlDetails")
            except:
                continue

        # Find detail table, collect master incident info
        incident_info = driver.find_element_by_id("tblDetails")
        incident_details = incident_info.find_elements_by_tag_name("tr")
        incident_num = incident_data.find_element_by_id("lblIncident").text
        incident_type = incident_data.find_element_by_id("lblType").text
        incident_loc = incident_data.find_element_by_id("lblLocation").text
        incident_loc_desc = incident_data.find_element_by_id("lblLocationDesc").text
        incident_id = "{}_{}".format(center, incident_num)
        try:
            incident_lat = incident_data.find_element_by_id("lblLatLon").text.split(
                " "
            )[0]
            incident_lng = incident_data.find_element_by_id("lblLatLon").text.split(
                " "
            )[1]
        except:
            incident_lat = ""
            incident_lng = ""
        selected_info = driver.find_element_by_class_name("gvSelected")
        selected_values = selected_info.find_elements_by_tag_name("td")
        incident_area = selected_values[6].text
        incident_time = selected_values[2].text

        # Excluding incident types
        if incident_type in type_exclusions:
            continue

        # Adding to incident df
        incident_dict = {
            "incident_id": incident_id,
            "chp_center": center,
            "incident_number": int(incident_num),
            "incident_type": incident_type,
            "incident_location": incident_loc,
            "incident_location_description": incident_loc_desc,
            "incident_area": incident_area,
            "incident_time": incident_time,
            "incident_lat": incident_lat,
            "incident_lng": incident_lng,
            "incident_tweet_id": 0,
        }

        # To be used in activity loop
        activity_list = []
        activity_ctr = 0
        activity_type = ""

        # Get activity for each incident
        for activity in incident_details:
            if (
                activity.text == "Detail Information"
                or activity.text == "Unit Information"
            ):
                activity_type = activity.text
                if "Detail" in activity_type:
                    activity_type_id = 1
                elif "Unit" in activity_type:
                    activity_type_id = 2
                else:
                    activity_type_id = 3
                continue
            else:
                activity_ctr += 1
                activity_data = activity.find_elements_by_tag_name("td")
                if activity_data[0].text == "NO DETAILS":
                    activity_dt = ""
                    activity_entry_num = 0
                    activity_text = ""
                    activity_id = "{}_{}".format(activity_type_id, activity_entry_num)
                else:
                    activity_dt = activity_data[0].text
                    activity_entry_num = activity_data[1].text
                    activity_text = activity_data[2].text
                    activity_id = "{}_{}".format(activity_type_id, activity_entry_num)

                # Excluding activity types
                if activity_type in activity_exclusions:
                    continue

                # Creating master key (incident, activity)
                incident_activity_id = "{}_{}_{}_{}".format(
                    center, incident_num, activity_type_id, activity_entry_num
                )

                # If not already in data, add to dict
                if incident_activity_id not in existing_activity:
                    new_activity_ctr += 1
                    activity_dict = {
                        "incident_activity_id": incident_activity_id,
                        "activity_id": activity_id,
                        "activity_type": activity_type,
                        "activity_dt": activity_dt,
                        "activity_num": int(activity_entry_num),
                        "activity_text": activity_text,
                        "activity_tweet_id": 0,
                    }
                    activity_list.append(activity_dict)

        # Check to make sure incident does not exist OR activity list contains items
        if incident_id not in existing_incidents:
            new_incident = True
            new_incident_ctr += 1
            print("Added {} new incident(s) for {}".format(new_incident_ctr, center))
        else:
            new_incident = False

        if len(activity_list) > 0:
            new_activity = True
            print("Added {} new activity for {}".format(new_activity_ctr, center))
        else:
            new_activity = False

        # Uploading incident
        if new_incident or new_activity:
            incident_dict["activity"] = activity_list
            upload_incident(incident_dict, new_incident, new_activity)
