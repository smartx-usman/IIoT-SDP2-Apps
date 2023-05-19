#!/bin/bash

White='\033[0;37m'
Red='\033[0;31m'
Green='\e[32m'
Yellow='\033[0;33m'
Blue='\e[34m'
BBlue='\e[44m'
FDefault='\e[49m'
NC='\033[0m' # No Color

LOGFILE="./setup.log"
exec 3>&1 1>"$LOGFILE" 2>&1

set -ex # Prints commands, prefixing them with a character stored in an environmental variable ($PS4)

trap "echo -e '$Red ERROR: An error occurred during execution, check log $LOGFILE for details.' >&3" ERR
trap '{ set +x; } 2>/dev/null; echo -n "[$(date -Is)]  "; set -x' DEBUG


while :
do
  echo -e "$Yellow Starting new cycle of experiments...${NC}" >&3

  echo -e "$BBlue Create namespaces...${NC}" >&3
    echo -e "$White Create ns sensor-pipeline..." >&3
      kubectl create namespace sensor-pipeline
    echo -e "$White Successfully created ns sensor-pipeline." >&3
    echo -e "$White Create ns flask-server..." >&3
      kubectl create namespace flask-server
    echo -e "$White Successfully created ns flask-server." >&3
    echo -e "$White Create ns file-server..." >&3
      kubectl create namespace file-server
    echo -e "$White Successfully created ns file-server." >&3
  echo -e "$BBlue Successfully created all the namespaces.${NC}" >&3

  echo -e "$BBlue Create Apps...${NC}" >&3
  echo -e "$White Create sensor-app..." >&3
  sh /home/aida/IIoT-SDP2-Apps/monitoring-anomly/sensor-app.sh
  sleep 60
  echo -e "$White Successfully created sensor-app." >&3

  echo -e "$White Create web-app..." >&3
  sh /home/aida/IIoT-SDP2-Apps/monitoring-anomly/web-app.sh
  sleep 60
  echo -e "$White Successfully created web-app." >&3

  echo -e "$White Create file-app..." >&3
  sh /home/aida/IIoT-SDP2-Apps/monitoring-anomly/file-app.sh
  sleep 60
  echo -e "$White Successfully created file-app." >&3
  echo -e "$BBlue Successfully created all Apps.${NC}" >&3

  echo -e "$BBlue Sleeping for 4 minutes..." >&3
  sleep 240
  echo -e "$BBlue Wakeup from sleep." >&3

  echo -e "$BBlue Delete namespaces...${NC}" >&3
    echo -e "$White Delete flask-server namespace..." >&3
      kubectl delete namespace flask-server
      sleep 60
    echo -e "$White Deleted flask-server namespace." >&3
    echo -e "$White Delete sensor-pipeline namespace..." >&3
      kubectl delete namespace sensor-pipeline
      sleep 60
    echo -e "$White Deleted sensor-pipeline namespace." >&3
    echo -e "$White Delete file-server namespace..." >&3
      kubectl delete namespace file-server
      sleep 60
    echo -e "$White Deleted file-server namespace." >&3
  echo -e "$BBlue Deleted all namespaces.${NC}" >&3

  echo -e "$Yellow Sleeping for 9 minutes..." >&3
  sleep 540
  echo -e "$Yellow Wakeup from sleep." >&3

  echo -e "$Green Current cycle of experiments completed.${NC}\n" >&3
done
