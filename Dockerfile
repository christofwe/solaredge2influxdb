FROM python:3.9-alpine

COPY . /app
RUN cd app/ && pip install -r requirements.txt
