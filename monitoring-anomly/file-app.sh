#!/bin/sh

kubectl apply -f /home/aida/IIoT-SDP2-Apps/file-server/file-server.yaml
sleep 10
kubectl apply -f /home/aida/IIoT-SDP2-Apps/file-server/file-client.yaml