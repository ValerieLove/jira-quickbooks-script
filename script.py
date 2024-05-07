import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import json
from tabulate import tabulate

load_dotenv()

#Variables
KEY = os.getenv('API_TOKEN')

MAKE_HOOK = os.getenv('MAKE_HOOK')
MAIL_HOOK = os.getenv('MAIL_HOOK')
CLOCKWORK_URL = os.getenv('CLOCKWORK_URL')
JIRA_URL = os.getenv('JIRA_URL')
JIRA_AUTH = HTTPBasicAuth(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_TOKEN'))
#User Account IDs
USERS_LIST = []
#Dictionary that maps User Account IDs to names
USERS_DICT = {}
#Times for each developer
TIMES_DICT = {}
#Times for each project
PROJECTS_DICT={}

# end_week = datetime.now()

# start_week = end_week - timedelta(days=5)



start_week = '2024-04-21'

end_week = '2024-04-27'


HEADERS = {
    'Authorization': f'Token {KEY}'
}
PARAMS = {
    'starting_at': start_week,
    'ending_at': end_week
}
#Call Clockwork API
clockwork_response = requests.get(url=CLOCKWORK_URL, headers=HEADERS, params=PARAMS)

if clockwork_response.status_code == 200:
    clockwork_response_list = clockwork_response.json()

    NAMES =['Vid Luther','Vitaliy Tikhonov','Jay Arredondo','Xuefeng Xi','Charles Rosas','Valeria Villanueva']
    USERS_DICT = {
        '70121:092a03e6-6aeb-47d6-9e75-611685238d30': 'Vid Luther', 
        '62ebea06432ef494c8ca69ec': 'Vitaliy Tikhonov', 
        '60df17578a72bd006c8fd71f': 'Jay Arredondo', 
        '5c46813254e1e6466b11c8ed': 'Xuefeng Xi', 
        '5f89f76957ca8c00766d9656': 'Charles Rosas', 
        '712020:285a9748-ecf9-4c88-ba6b-036f4394c81d': 'Valeria Villanueva'
    }


    TIMES_DICT = {k:v for k,v in zip(NAMES, [0 for name in NAMES])}
    ISSUES_DICT={k:v for k, v in zip(NAMES, [[] for name in NAMES])}

    #Set up Payloads
    for id in clockwork_response_list:
        TIMES_DICT[USERS_DICT[id['author']['accountId']]] += id['timeSpentSeconds']
        ISSUES_DICT[USERS_DICT[id['author']['accountId']]].append(id['issueId'])
        jira_response = requests.get(url=f"{JIRA_URL}{id['issueId']}", headers={'Accept':'application/json'}, auth=JIRA_AUTH)
        if jira_response.status_code == 200:
            PROJECTS_DICT.setdefault(jira_response.json()['fields']['project']['key'], 0)
            PROJECTS_DICT[jira_response.json()['fields']['project']['key']] += id['timeSpentSeconds']
        else:
            print(f'Error: Jira exited with code: {jira_response.status_code}')
            exit(0)


    FINAL_PAYLOAD = []

    for name in NAMES:
        FINAL_PAYLOAD.append({'name': name, 'time_hours': int(TIMES_DICT[name]/3600), 'time_minutes': int((TIMES_DICT[name] % 3600)/60), 'issues': ISSUES_DICT[name]})

    PROJECTS_DICT_LIST = [(key, f"{int(PROJECTS_DICT[key]/3600)}h {int((PROJECTS_DICT[key] % 3600)/60)}m") for key in PROJECTS_DICT]

    print(tabulate([[i['name'], f"{i['time_hours']}h {i['time_minutes']}m", len(i['issues'])] for i in FINAL_PAYLOAD], headers=['Name', 'Time', 'Number of Issues']))
    print(tabulate(PROJECTS_DICT_LIST, headers=['Project', 'Time']))
    print(FINAL_PAYLOAD)
    choice = input("Send times? (y/n):\t")
    
    if choice == 'n':
        exit(0)
    
    hook_response = requests.post(url=MAKE_HOOK, headers={'Content-Type':'application/json'}, data=json.dumps(FINAL_PAYLOAD))
    if hook_response.status_code == 200:
        print("Sent to make!")
    else:
        print(f"Error: Make.com exited with status code: {hook_response.status_code}")
        exit(0)

else:
    print(f"Error: Clockwork exited with status code: {clockwork_response.status_code}")

PROJECT_TIMES_PAYLOAD =[{"project": key, "time_hours": int(PROJECTS_DICT[key]/3600), "time_minutes": int((PROJECTS_DICT[key] % 3600)/60)} for key in PROJECTS_DICT]
PROJECTS_DICT = {}
print(json.dumps(PROJECT_TIMES_PAYLOAD))

choice = input("Send Payload? (y/n): ")

if choice == 'n':
    exit(0)

mailhook_response = requests.post(url=MAIL_HOOK, headers={'Content-Type':'application/json'}, data=json.dumps(PROJECT_TIMES_PAYLOAD))

if mailhook_response.status_code == 200:
    print("Project totals sent")
else:
    print(f"Error: Make.com email scenario exited with code: {mailhook_response.status_code}")








