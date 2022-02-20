# solaredge2influxdb

Simple container that queries Solaredge's(https://www.solaredge.com/) API and writes metrics to a (local) influxDB.

## Requirements:
- Docker execution runtime
- SolarEdge inverter

## Steps
1. Copy `.env.sample` to `.env` and update w/ actual values
2. Run `docker-compose up -d`