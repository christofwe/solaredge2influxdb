import os
import requests

from datetime import datetime

from influxdb import InfluxDBClient

INFLUXDB_HOST = os.environ['INFLUXDB_HOST']
INFLUXDB_PORT = os.environ['INFLUXDB_PORT']
INFLUXDB_USER = os.environ['INFLUXDB_USER']
INFLUXDB_PASS = os.environ['INFLUXDB_PASS']
INFLUXDB_DB_NAME = os.environ['INFLUXDB_DB_NAME']

SOLAREDGE_API = os.environ['SOLAREDGE_API']
SOLAREDGE_API_KEY = os.environ['SOLAREDGE_API_KEY']
SOLAREDGE_ID = os.environ['SOLAREDGE_ID']

solaredge_api_base_url = f"{SOLAREDGE_API}"
solaredge_headers = {'Content-Type': 'application/json'}
solaredge_params = {'api_key': SOLAREDGE_API_KEY}

local = datetime.now()
timestamp = local.strftime("%Y-%m-%dT%H:%M:%SZ")

if local.hour == 12:
  influx_client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USER, password=INFLUXDB_PASS)
  influx_client.switch_database(INFLUXDB_DB_NAME)

  json_body = []

  try:
    data_period_response = requests.get(f"{SOLAREDGE_API}/site/{SOLAREDGE_ID}/dataPeriod", headers=solaredge_headers, params=solaredge_params)
    data_period_response.raise_for_status()
    data_period = data_period_response.json()

    solaredge_params.update(data_period['dataPeriod'])
    solaredge_params.update({'timeUnit': 'MONTH'})
    energy_response = requests.get(f"{SOLAREDGE_API}/site/{SOLAREDGE_ID}/energy", headers=solaredge_headers, params=solaredge_params)
    energy_response.raise_for_status()
    energy = energy_response.json()

    for value in energy['energy']['values']:
      item = {
        "measurement": "Production",
        "tags": {
          "type": "report"
        },
        "time": value['date'],
        "fields": {
          "Wh": value['value']
        }
      }
      json_body.append(item)

    influxdb_write = influx_client.write_points(json_body)
    print(f"{timestamp} influxdb_write: {influxdb_write}")

  except requests.exceptions.HTTPError as error:
    print(f"solaredge error: {error}")
    print(f"data_period_response status_code: {data_period_response.status_code}")
    print(f"energy_response status_code: {energy_response.status_code}")
