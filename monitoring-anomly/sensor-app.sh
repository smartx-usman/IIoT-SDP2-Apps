#!/bin/sh

helm repo add t3n https://storage.googleapis.com/t3n-helm-charts
helm -n sensor-pipeline upgrade --install mqtt -f /home/aida/IIoT-SDP2-Apps/sensor-data-pipeline/brokers/mqtt-values.yaml t3n/mosquitto
sleep 10

helm repo add bitnami https://charts.bitnami.com/bitnami
helm upgrade --install bitnami -n sensor-pipeline -f /home/aida/IIoT-SDP2-Apps/sensor-data-pipeline/brokers/kafka-values.yaml bitnami/kafka
sleep 10

helm upgrade --install mysql -n=sensor-pipeline -f /home/aida/IIoT-SDP2-Apps/sensor-data-pipeline/datastores/mysql-values.yaml bitnami/mysql
sleep 10

kubectl apply -n sensor-pipeline -f /home/aida/IIoT-SDP2-Apps/sensor-data-pipeline/kubernetes/data-generator-job.yaml
sleep 5

kubectl apply -n sensor-pipeline -f /home/aida/IIoT-SDP2-Apps/sensor-data-pipeline/kubernetes/publisher-deployment-normal.yaml
sleep 10

kubectl apply -n sensor-pipeline -f /home/aida/IIoT-SDP2-Apps/sensor-data-pipeline/kubernetes/subscriber-deployment.yaml
sleep 5

kubectl apply -n sensor-pipeline -f /home/aida/IIoT-SDP2-Apps/sensor-data-pipeline/kubernetes/temp-analyzer-deployment.yaml
sleep 5

kubectl apply -n sensor-pipeline -f /home/aida/IIoT-SDP2-Apps/sensor-data-pipeline/kubernetes/temp-actuator-deployment.yaml