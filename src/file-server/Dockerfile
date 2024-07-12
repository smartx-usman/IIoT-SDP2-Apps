FROM python:3.9-slim-buster

WORKDIR /app

RUN apt -y update && apt -y install wget
RUN pip3 install requests

COPY file-server.py .
COPY file-client.py .
