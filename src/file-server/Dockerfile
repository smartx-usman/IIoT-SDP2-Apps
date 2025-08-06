FROM python:3.13-slim

WORKDIR /app

RUN apt update && apt -y install wget
RUN pip3 install requests

COPY file-server.py .
COPY file-client.py .
