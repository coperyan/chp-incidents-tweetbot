import requests
import os
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import time

from chp_data import get_chp_centers, get_incident_df, save_incident_df
from chp_data import get_incident_activity_df, save_incident_activity_df

driver_path = '/Users/rcope/Downloads/chromedriver'
incidents_url = 'https://cad.chp.ca.gov/Traffic.aspx'

chp_centers = get_chp_centers()
incident_df = get_incident_df()
incident_activity_df = get_incident_activity_df()

ignored_exceptions=(NoSuchElementException,StaleElementReferenceException,)

#Function to get incidents
#Update dataframes with NEW incidents or activity
def get_incidents():
    driver = webdriver.Chrome(executable_path=driver_path)
    driver.get(incidents_url)

    #Disable auto refresh on page (this may not work)
    auto_refresh = driver.find_element_by_id('chkAutoRefresh')
    auto_refresh.click()    

    #Find incidents for each CHP center
    for center in chp_centers:
        print('Getting incidents for center {}'.format(center))

        #Select center
        center_dd = Select(driver.find_element_by_id('ddlComCenter'))
        center_dd.select_by_visible_text(center)

        #Find incidents (if none, continue loop)
        try:
            incidents_table = driver.find_element_by_id('gvIncidents')
            incidents_rows = incidents_table.find_elements_by_tag_name('tr')
        except:
            continue

        #Remove header BS
        incidents_rows = incidents_rows[1:]

        #Have to create list of incident numbers instead of element reference
        incidents_list = []
        for row in incidents_rows:
            incidents_list.append(row.find_elements_by_tag_name('td')[1].text)
        incident_ct = len(incidents_list)
        print('{} incident(s) found for center {}'.format(incident_ct,center))

        #Get details for each incident
        for incident in incidents_list:

            #Need to rediscover element based on matching incident ID
            incidents_table = driver.find_element_by_id('gvIncidents')
            incidents_rows = incidents_table.find_elements_by_tag_name('tr')
            incidents_rows = incidents_rows[1:]
            for row in incidents_rows:
                if row.find_elements_by_tag_name('td')[1].text == incident:
                    incident_row = row
                    break

            #Click detail href and expand details - sometimes this fails and we need to try twice
            try:
                detail_href = incident_row.find_element_by_tag_name('a')
                detail_href.click()
                incident_data = driver.find_element_by_id('pnlDetails')
            except:
                try:
                    time.sleep(10)
                    detail_href = incident_row.find_element_by_tag_name('a')
                    detail_href.click()
                    incident_data = driver.find_element_by_id('pnlDetails')
                except:
                    continue

            #Find detail table, collect master incident info
            incident_info = driver.find_element_by_id('tblDetails')
            incident_details = incident_info.find_elements_by_tag_name('tr')
            incident_num = incident_data.find_element_by_id('lblIncident').text
            incident_type = incident_data.find_element_by_id('lblType').text
            incident_loc = incident_data.find_element_by_id('lblLocation').text
            incident_loc_desc = incident_data.find_element_by_id('lblLocationDesc').text
            incident_id = '{}_{}'.format(center,incident_num)
            try:
                incident_lat = incident_data.find_element_by_id('lblLatLon').text.split(' ')[0]
                incident_lng = incident_data.find_element_by_id('lblLatLon').text.split(' ')[1]
            except:
                incident_lat = ''
                incident_lng = ''

            #Adding to incident df
            if incident_id not in incident_df['incident_id'].values:
                incident_df.loc[len(incident_df)] = [
                    incident_id,
                    center,
                    incident_num,
                    incident_type,
                    incident_loc,
                    incident_loc_desc,
                    incident_lat,
                    incident_lng,
                    ''
                ] 

            #Get activity for each incident
            activity_ctr = 0
            activity_type = ''
            for activity in incident_details:
                if activity.text == 'Detail Information' or activity.text == 'Unit Information':
                    activity_type = activity.text
                    continue
                else:
                    activity_ctr += 1
                    activity_data = activity.find_elements_by_tag_name('td')
                    if activity_data[0].text == 'NO DETAILS':
                        activity_id = activity_ctr
                        activity_dt = ''
                        activity_entry_num = ''
                        activity_text = ''
                    else:
                        activity_id = activity_ctr
                        activity_dt = activity_data[0].text
                        activity_entry_num = activity_data[1].text
                        activity_text = activity_data[2].text

                    #Creating master key (incident, activity)
                    incident_activity_id = '{}_{}_{}'.format(center,incident_num,activity_id)

                    #If not already in data, add to dataframe
                    if incident_activity_id not in incident_activity_df['incident_activity_id'].values:
                        incident_activity_df.loc[len(incident_activity_df)] = [
                            incident_activity_id,
                            incident_id,
                            activity_id,
                            activity_type,
                            activity_dt,
                            activity_entry_num,
                            activity_text,
                            '',
                            ''
                        ]

    save_incident_df(incident_df)
    save_incident_activity_df(incident_activity_df)
                


