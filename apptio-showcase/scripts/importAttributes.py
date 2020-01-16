import json
import requests
import pandas as pd

api_token = 'hc5ydyWcWsMZVbktNdNuY4DcmOsqFMMWCCGGdT5x'
auth_url = 'https://app.leanix.net/services/mtm/v1/oauth2/token'
request_url = 'https://demo-eu.leanix.net/services/integration-api/v1/'

# Get the bearer token - see https://dev.leanix.net/v4.0/docs/authentication
response = requests.post(auth_url, auth=('apitoken', api_token),
                         data={'grant_type': 'client_credentials'})
response.raise_for_status()
header = {'Authorization': 'Bearer ' + response.json()['access_token'], 'Content-Type': 'application/json'}


def createRun(processors, content):
    data = {
        "connectorType": "ee",
        "connectorId": "Dev",
        "connectorVersion": "0.1",
        "lxVersion": "1.0.0",
        "description": "Imports kubernetes data into LeanIX",
        "processingDirection": "inbound",
        "processingMode": "partial",
        "customFields": customFields,
        "content": content
    }

    print(data)
    response = requests.post(url=request_url + 'synchronizationRuns/', headers=header, data=json.dumps(data))
    print(response.json())
    return (response.json())


def startRun(run):
    response = requests.post(url=request_url + 'synchronizationRuns/' + run['id'] + '/start?test=false', headers=header)


def status(run):
    response = requests.get(url=request_url + 'synchronizationRuns/' + run['id'] + '/status', headers=header)
    return (response.json())


def getResults(run):
    response = requests.get(url=request_url + 'synchronizationRuns/' + run['id'] + '/results', headers=header)

    if response.status_code == 204:
        print("No result content available for run: " + run['id'])
    else:
        return (response.json())


def processor(fsType):
    return {
        "processorType": "inboundFactSheet",
        "processorName": "Apps from Deployments",
        "processorDescription": "My description",
        "run": 0,
        "type": fsType,
        "identifier": {
            "external": {
                "id": "${content.id}",
                "type": "externalId"
            }
        },
        "filter": {"type": fsType},
        "updates": [{"key": {"expr": "name"}, "values": [{"expr": "${data.name}"}]}]
    }


def relationProcessor(fsType, rel):
    return {
        "processorType": "inboundRelation",
        "processorName": "Rel from Apps to ITComponent",
        "processorDescription": "My description",
        "filter": {
            "type": fsType
        },
        "run": 1,
        "type": rel,
        "from": {
            "external": {
                "type": "externalId",
                "id": "${content.id}"
            }
        },
        "to": {
            "external": {
                "type": "externalId",
                "id": "${data.itc}"
            }
        }
    }


# 1. Read input from XLS
df = pd.read_excel('data/input_attribute.xlsx', sheet_name='Sheet1', sep=';')
apps = df[['Application', 'TOC', 'CapEx', 'OpEx', 'RunCost', 'ChangeCost']]
itcs = df[['ITComponent']]
appToITC = {}
for index, row in df.iterrows():
    appToITC[row['Application']] = row['ITComponent']

# 2. Setup content  appToITC[app[1]]
customFields = {}
content = []
for index, row in apps.iterrows():
    content.append({
        "type": "Application",
        "id": row['Application'],
        "data": {"name": row['Application'], "totalCostOfOwnership": row['TOC'], "capEx": row['CapEx'], "opEx": row['OpEx'], "runCost": row['RunCost'], "changeCost": row['ChangeCost']}
    })
for itc in itcs:
    content.append({
        "type": "ITComponent",
        "id": itc,
        "data": {"name": itc}
    })

# 3. Setup processors
processors = [
    processor('Application'),
    processor('ITComponent'),
    relationProcessor('Application', 'relApplicationToITComponent')
]

# 4. Start run and fetch results
run = createRun(processors, content)
startRun(run)
while (True):
    if (status(run)['status'] == 'FINISHED'): break

resp = getResults(run)
if resp:
    for result in getResults(run):
        print(str(result['content']) + ' ' + str(result['errors']))
