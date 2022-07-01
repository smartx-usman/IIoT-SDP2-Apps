#!/bin/bash

option=$1

if [[ -z $option ]]; then
  echo "No parameter passed."
else
  echo "Parameter passed to $1 applications."
fi

if [[ $option = 'create' ]]; then
  echo 'Creating namespaces:'
  for application in {0..5}; do
    kubectl create namespace uc$application
  done

  echo 'Add Helm repos:'
  helm repo add t3n https://storage.googleapis.com/t3n-helm-charts
  helm repo add bitnami https://charts.bitnami.com/bitnami

  echo 'Deploying tools via Helm:'
  for application in {1..5}; do
    helm upgrade --install -n uc$application mqtt -f mqtt-broker/mqtt-values.yaml t3n/mosquitto
    helm upgrade --install -n uc$application bitnami -f kafka-broker/kafka-values.yaml bitnami/kafka
  done
  sleep 30

  #for application in {1..5}; do
  #  helm upgrade --install -n uc$application cassandra -f datastores/cassandra-values.yaml bitnami/cassandra
  #done

  echo 'Deploying the tools via Kubectl:'
  kubectl apply --namespace=uc0 -f generator/data-generator-job.yaml

  sleep 10



  for application in {1..5}; do
    sed -i "s/uc0/uc$application/" publisher/mqtt-publisher-deployment.yaml
    sed -i "s/uc0/uc$application/" subscriber/mqtt-subscriber-pod.yaml
    sed -i "s/uc0/uc$application/" analyzer/temp-analyzer-pod.yaml
    sed -i "s/uc0/uc$application/" actuator/temp-actuator-pod.yaml

    kubectl apply --namespace=uc$application -f publisher/mqtt-publisher-deployment.yaml
    kubectl apply --namespace=uc$application -f subscriber/mqtt-subscriber-pod.yaml
    kubectl apply --namespace=uc$application -f analyzer/temp-analyzer-pod.yaml
    kubectl apply --namespace=uc$application -f actuator/temp-actuator-pod.yaml

    sed -i "s/uc$application/uc0/" publisher/mqtt-publisher-deployment.yaml
    sed -i "s/uc$application/uc0/" subscriber/mqtt-subscriber-pod.yaml
    sed -i "s/uc$application/uc0/" analyzer/temp-analyzer-pod.yaml
    sed -i "s/uc$application/uc0/" actuator/temp-actuator-pod.yaml

    sleep 10
  done

elif [[ $option = 'delete' ]]; then
  echo 'Remove all deployed applications:'
  for application in {0..5}; do
    kubectl delete namespace uc$application
  done

else
  echo "Provide a valid option to run the script. E.g., ./create_experimental_setup.sh create"
fi
