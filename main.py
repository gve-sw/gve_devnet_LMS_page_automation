# Copyright (c) 2021 Cisco and/or its affiliates.

# This software is licensed to you under the terms of the Cisco Sample
# Code License, Version 1.1 (the "License"). You may obtain a copy of the
# License at

#                https://developer.cisco.com/docs/licenses

# All use of the material herein must be in accordance with the terms of
# the License. All rights not expressly granted by the License are
# reserved. Unless required by applicable law or agreed to separately in
# writing, software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.

import csv
import smartsheet
import os
import requests
import config
from selenium import webdriver
from bs4 import BeautifulSoup
import time


#### CONFIG ####
CSV_FILE_NAME = config.CSV_FILE_NAME
HTML_FILE_NAME = config.HTML_FILE_NAME

SMARTSHEET_ACCESS_TOKEN = config.SMARTSHEET_ACCESS_TOKEN
SMARTSHEET_SHEET_ID = config.SMARTSHEET_SHEET_ID

COLE_ACCESS_TOKEN = config.COLE_ACCESS_TOKEN
COLE_URL = config.COLE_URL
COLE_PAGE_TITLE = config.COLE_PAGE_TITLE

LINKEDIN_EMAIL = config.LINKEDIN_EMAIL
LINKEDIN_PASSWORD = config.LINKEDIN_PASSWORD

BROWSER = webdriver.Chrome(executable_path=config.CHROMEDRIVER_PATH)

ASE_COLOR = "#f4ad3f"
ASR_COLOR = "#d73c29"

DEFAULT_PROFILE = "https://img.icons8.com/ios/452/baby-yoda.png"
#### CONFIG ####

# Retrieve Smartsheet data in CSV format
def get_smartsheet_as_csv():
    path = os.getcwd()
    smart = smartsheet.Smartsheet(access_token=SMARTSHEET_ACCESS_TOKEN)
    sheet = smart.Sheets.get_sheet(sheet_id=SMARTSHEET_SHEET_ID)
    filename = sheet.name + '.csv'
    smart.Sheets.get_sheet_as_csv(sheet_id=SMARTSHEET_SHEET_ID, download_path=path)
    return filename

# Create JSON format for CSV data fetched from Smartsheet
def read_csv(filename):
    with open(filename) as csv_file:
        column_names = ["Your name"]
        associates = {}

        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                for i in range(1,len(row)):
                    column_names += [row[i]]
                line_count += 1
            else:
                associate = {}
                associate["Your name"] = row[0]
                for i in range(len(column_names)):
                    associate[column_names[i]] = row[i]
                if associate["Your theatre"] in associates:
                    associates[associate["Your theatre"]] += [associate]
                else:
                    associates[associate["Your theatre"]] = [associate]
                line_count += 1
        print(f'Processed {line_count} lines.')
        return associates
    return []

# Turn one associate's JSON object into HTML code
def associate_to_html(associate):
    linkedin_pic = DEFAULT_PROFILE
    try: 
        linkedin_pic = fetch_linkedin_pic(associate["LinkeIn Profile URL"])
    except: 
        print("Missed one")
    
    if (not linkedin_pic.startswith("http")):
        linkedin_pic = DEFAULT_PROFILE
    
    color = ASE_COLOR
    if "ASR" in associate["CSAP track"]:
        color = ASR_COLOR

    result = \
    r"""
    <div style="position: relative; vertical-align: top; overflow: hidden; background-color: #ebebeb; margin: 5px; padding: 20px; display: inline-block; min-width: 235px; max-width: 235px; min-height: 529px; max-height: 529px;"><span style="background-color: """ + \
    color + \
    r"""; text-align: left; font-weight: bold; padding: 4px; color: white; position: absolute; float: right; top: 10px; right: 10px;">""" \
    + associate["CSAP track"] + \
    r"""</span>
    <div style="width: 100%; text-align: center; min-height: 235px;">
    <img src=" """ \
    + linkedin_pic + \
    r""" " width="100%" align="middle" /></div>
    <p style="text-align: center;"><span style="font-size: 18px; font-weight: bold;">""" \
    + associate["Your name"] + \
    r"""</span><br />
    <span style="font-style: italic;">""" \
    + f'{associate["Your city of residence"]}, {associate["Your country of residence"]}' + \
    r"""</span><br />
    <a style="line-height:30px;" class="inline_disabled" target="_blank" href=" """ \
    + associate["Your video Advice"] + r""" "><img style="vertical-align: middle; height: 20px;" src="https://image.flaticon.com/icons/png/512/0/375.png" /></a>
    <a target="_blank" href="mailto:""" + f'{associate["Your CEC"]}@cisco.com'r""" "><img style="vertical-align: middle; height: 20px;" src="https://toppng.com/uploads/preview/email-icon-vector-circle-11549825158ieiklzfl8g.png" /></a>
    <a target="_blank" href=" """ \
    + associate["LinkeIn Profile URL"] + \
    r""" "><img style="vertical-align: middle; height: 20px;" src="https://sguru.org/wp-content/uploads/2018/02/linkedin-png-linkedin-icon-1600.png" /></a>
    <br />
    </p>
    <div style="text-align: center; font-size: 12px; font-style: italic;">" """ \
    + associate["Reach out to me if..."] + \
    r""" "</div>
    <div style="text-align: center; font-size: 12px; font-style: bold;margin-top:20px;line-height: 150%;">""" \
    + studies_string(associate) \
    + interest_string(associate["Your personal interests (choose between 1 and 3)"]) \
    + interest_string(associate["If other interest:"]) \
    + strength_string(associate["General Strengths (choose between 1 and 3)"]) \
    + strength_string(associate["If other strength:"]) + \
    r"""</div>
    <p>&nbsp;</p>
    </div>
    """
    return result

# Generate string for interests
def interest_string(interests):
    result = ""
    for i in interests.split('\n'):
        if (i != "Other" and len(i) > 1):
            result += r'<span style="white-space:nowrap; background-color: #00bceb; margin-left:5px; color:white; ">&nbsp' + i + r"&nbsp</span>"
    return result

# Generate string for strengths
def strength_string(strengths):
    result = ""
    for i in strengths.split('\n'):
        if (i != "Other" and len(i) > 1):
            result += r'<span style="white-space:nowrap; background-color: #6cc04a; margin-left:5px; color:white; ">&nbsp' + i + r"&nbsp</span>"
    return result

# Generate string for studies
def studies_string(associate):
    result = associate["Your major/degree"]
    if result == "Other":
        result = associate["If other major/degree:"]
    return r'<span style="white-space:nowrap; background-color: #e2231a; margin-left:5px; color:white; ">&nbspDegree:&nbsp' + result + r"&nbsp</span>"

# Generate theatre preamble
def preamble(theatre):
    return r"""
    <div>
    <h2 style="margin-top: 30px; padding: 5px; color: #ffffff; background-color: #155070; min-width: 100%;">""" \
    + theatre + \
    r"""</h2>"""

# Post HTML page to COLE
def post_html_to_cole(raw_data):
    data = {}
    headers = {}
    headers['Authorization'] = 'Bearer ' + COLE_ACCESS_TOKEN

    data["wiki_page[title]"] = COLE_PAGE_TITLE
    data["wiki_page[body]"] = raw_data

    requests.put(COLE_URL, data=data, headers=headers)

# Scrape LinkedIn for profile picture URL
def fetch_linkedin_pic(profile_url): 
    # Load the page on the browser
    if str.startswith(profile_url, "http"):
        BROWSER.get(profile_url)
    else:
        BROWSER.get(f"https://{profile_url}")

    # Load page
    time.sleep(2)

    # Rendering the page
    soup = BeautifulSoup(BROWSER.page_source, 'lxml')

    # Scraping the name
    name_div = soup.find('div', {'class': 'pv-text-details__left-panel mr5'})
    print(name_div)
    name = name_div.find('h1', {'class': "text-heading-xlarge inline t-24 v-align-middle break-words"}).text.strip()
    print(name)

    # Scraping the picture
    picture = soup.find_all(attrs={"alt" : name})[0]
    profile_pic_url = picture.get_attribute_list("src")[0]
    print(profile_pic_url)
    return profile_pic_url

# Setup browser for LinkedIn fetching
def browser_setup():
    BROWSER.get("https://www.linkedin.com")
    time.sleep(2)

    # Enter email
    username = BROWSER.find_elements_by_class_name('input__input')[0]
    username.send_keys(LINKEDIN_EMAIL)

    # Enter password
    password = BROWSER.find_elements_by_class_name('input__input')[1]
    password.send_keys(LINKEDIN_PASSWORD)

    # Click submit
    log_in_button = BROWSER.find_element_by_class_name('sign-in-form__submit-button')
    log_in_button.click()

    time.sleep(5)

#### MAIN ####
if __name__ == "__main__":
    browser_setup()

    # Fetch Smartsheet data as CSV
    filename = get_smartsheet_as_csv()
    
    # Construct HTML file
    file = r""
    associates = read_csv(filename)
    for theatre in associates:
        file += preamble(theatre)
        sorted_associates = sorted(associates[theatre], key=lambda k: k['Your country of residence'])
        for associate in sorted_associates:
            file += associate_to_html(associate)
    
    BROWSER.quit()
    
    # Write HTML file to local file system
    f = open(HTML_FILE_NAME, "w")
    f.write(file)
    f.close()
    
    # Post HTML file to COLE
    post_html_to_cole(file)
#### MAIN ####

    