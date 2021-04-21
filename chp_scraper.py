import requests
import os
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from chp_data import get_chp_centers, get_incident_df

driver_path = '/Users/rcope/Downloads/chromedriver'
incidents_url = 'https://cad.chp.ca.gov/Traffic.aspx'

chp_centers = get_chp_centers()
incident_df = get_incident_df()

ignored_exceptions=(NoSuchElementException,StaleElementReferenceException,)

def get_driver():
    driver = webdriver.Chrome(executable_path=driver_path)
    return driver

#def get_incidents():
driver = get_driver()
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

        #Click detail href and expand details
        detail_href = incident_row.find_element_by_tag_name('a')
        detail_href.click()
        incident_data = driver.find_element_by_id('pnlDetails')
        incident_info = driver.find_element_by_id('tblDetails')
        incident_details = incident_info.find_elements_by_tag_name('tr')
        incident_num = incident_data.find_element_by_id('lblIncident').text
        incident_type = incident_data.find_element_by_id('lblType').text
        incident_loc = incident_data.find_element_by_id('lblLocation').text
        incident_loc_desc = incident_data.find_element_by_id('lblLocationDesc').text
        incident_lat = incident_data.find_element_by_id('lblLatLon').text.split(' ')[0]
        incident_lng = incident_data.find_element_by_id('lblLatLon').text.split(' ')[1]

        #Get activity for each incident
        activity_type = ''
        for activity in incident_details:
            if activity.text == 'Detail Information' or activity.text == 'Unit Information':
                activity_type = activity.text
                continue
            else:
                activity_data = activity.find_elements_by_tag_name('td')
                if activity_data[0].text == 'NO DETAILS':
                    activity_dt = ''
                    activity_entry_num = ''
                    activity_text = ''
                else:
                    activity_dt = activity_data[0].text
                    activity_entry_num = activity_data[1].text
                    activity_text = activity_data[2].text

                #Add data to dataframe
                incident_df.loc[len(incident_df)] = [
                    center,
                    incident_num,
                    incident_type,
                    incident_loc,
                    incident_loc_desc,
                    incident_lat,
                    incident_lng,
                    activity_type,
                    activity_dt,
                    activity_entry_num,
                    activity_text
                ]
                

#get_incidents()


##TESTING

# driver = get_driver()
# driver.get(incidents_url)
# test = Select(driver.find_element_by_id('ddlComCenter'))
# test.select_by_visible_text('Chico')
# auto_refresh = driver.find_element_by_id('chkAutoRefresh')
# auto_refresh.click()
# table = driver.find_element_by_id('gvIncidents')
# rows = table.find_elements_by_tag_name('tr')
# rows = rows[1:]

# row_test = rows[1] #rows[0] is header
# row_detail = row_test.find_element_by_tag_name('a')
# row_detail.click()
# detail_data = driver.find_element_by_id('pnlDetails')
# incident_num = detail_data.find_element_by_id('lblIncident').text
# incident_type = detail_data.find_element_by_id('lblType').text
# incident_loc = detail_data.find_element_by_id('lblLocation').text
# incident_loc_desc = detail_data.find_element_by_id('lblLocationDesc').text
# incident_lat = detail_data.find_element_by_id('lblLatLon').text.split(' ')[0]
# incident_lng = detail_data.find_element_by_id('lblLatLon').text.split(' ')[1]
# detail_table = driver.find_element_by_id('tblDetails')
# detail_table_rows = detail_table.find_elements_by_tag_name('tr')
#need to loop over rows - detail first, then units assigned (header will tell us what changes)