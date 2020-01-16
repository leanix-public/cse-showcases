import json 
import requests 
import pandas as pd
from scripts import getFactsheets as fs
import random

api_token = 'aRFZ5MqjZvVRrDemVmYSAN3PwgLmjVZW3kwOygxU'
ws_id = 'ea7d3162-b4c5-4dbf-b9fb-6ba8f050ce08'
auth_url = 'https://app.leanix.net/services/mtm/v1/oauth2/token' 
request_url = 'https://app.leanix.net/services/metrics/v1/points'

# Get the bearer token - see https://dev.leanix.net/v4.0/docs/authentication
response = requests.post(auth_url, auth=('apitoken', api_token),
                         data={'grant_type': 'client_credentials'})
response.raise_for_status() 
access_token = response.json()['access_token']
auth_header = 'Bearer ' + access_token
header = {'Authorization': auth_header, 'Content-Type': 'application/json'}
  
df = pd.read_excel('input_metric.xlsx', sheet_name='Worksheet', sep=';')

factsheets = []
response_gAFQ = fs.getAllFactsheetsQuery();
for node in fs.getGraphQl(response_gAFQ,access_token)['data']['allFactSheets']['edges']:
    factsheets.append(node['node']['id'])

for index, row in df.iterrows():
    for key in factsheets:
      data = {
          "measurement": row['measurement'],
          "workspaceId": ws_id,
          "time": row['date'].strftime('%Y-%m-%d') + "T00:00:00.000Z",
          "tags": [
            {
              "k": "factSheetId",
              "v": str(key)
            }
          ],
          "fields": [
            {
              "k": row['key'],
              "v": str(random.randrange(1000, 10000))
            }
          ]
        }
      json_data = json.dumps(data)
      print(data)
      response = requests.post(url=request_url, headers=header, data=json_data)

      response.raise_for_status()
      print(response.json())



