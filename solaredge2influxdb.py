import os
import requests

from datetime import datetime, timedelta
import pytz

from influxdb import InfluxDBClient

INFLUXDB_HOST = os.environ['INFLUXDB_HOST']
INFLUXDB_PORT = os.environ['INFLUXDB_PORT']
INFLUXDB_USER = os.environ['INFLUXDB_USER']
INFLUXDB_PASS = os.environ['INFLUXDB_PASS']
INFLUXDB_DB_NAME = os.environ['INFLUXDB_DB_NAME']

SOLAREDGE_API = os.environ['SOLAREDGE_API']
SOLAREDGE_API_KEY = os.environ['SOLAREDGE_API_KEY']
SOLAREDGE_ID = os.environ['SOLAREDGE_ID']


tz = pytz.timezone(os.environ['TZ'])
local = tz.localize(datetime.now())
timestamp = local.strftime("%Y-%m-%dT%H:%M:%S%Z%z")

influx_client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USER, password=INFLUXDB_PASS)
influx_client.switch_database(INFLUXDB_DB_NAME)
influx_body = []

solaredge_api_base_url = f"{SOLAREDGE_API}"
solaredge_headers = {'Content-Type': 'application/json'}
solaredge_params = {
  'api_key': SOLAREDGE_API_KEY,
  'startDate': (local - timedelta(days=1)).strftime("%Y-%m-%d"),
  'endDate': local.strftime("%Y-%m-%d")
}
daily_energy = {}
monthly_energy = {}

def get_site_energy(time_unit, headers, params):
  params.update({'timeUnit': time_unit})
  site_energy = requests.get(f"{SOLAREDGE_API}/site/{SOLAREDGE_ID}/energy", headers=headers, params=params)
  site_energy.raise_for_status()
  return site_energy.json()

def generate_data_points(energy):
  data_points = []
  time_unit = energy['energy']['timeUnit']
  unit = energy['energy']['unit']
  for value in energy['energy']['values']:
    timestamp = tz.localize(datetime.fromisoformat(value['date']))
    data_point = {
      "measurement": f"production_{time_unit}",
      "tags": {
        "type": "report",
        "period": time_unit
      },
      "time": timestamp.isoformat(),
      "fields": {
        unit: value['value']
      }
    }
    data_points.append(data_point)
  return data_points

if local.hour == 1:
  influx_body.extend(generate_data_points(get_site_energy("DAY", solaredge_headers, solaredge_params)))

if local.day == 1:
  influx_body.extend(generate_data_points(get_site_energy("MONTH", solaredge_headers, solaredge_params)))

if influx_body:
  influxdb_write = influx_client.write_points(influx_body)
  print(f"{timestamp} influxdb_write: {influxdb_write}")
else:
  print(f"{timestamp} influxdb_write: no")
