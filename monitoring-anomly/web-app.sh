#!/bin/sh

kubectl apply -n flask-server -f /home/aida/IIoT-SDP2-Apps/web-server/flask.yaml
sleep 10
kubectl apply -n flask-server -f /home/aida/IIoT-SDP2-Apps/web-server/client.yaml