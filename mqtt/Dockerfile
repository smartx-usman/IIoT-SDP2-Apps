FROM python:3.8-slim

ENV SENSORS="1"
ENV MESSAGE_DELAY="0.5"
ENV MQTT_BROKER="mqtt-mosquitto.uc0.svc.cluster.local"
ENV MQTT_BROKER_PORT="1883"
ENV MQTT_SENSOR_TOPIC="mqtt/temperature/readings"
ENV MQTT_ACTUATOR_TOPIC="mqtt/temperature/actions"
ENV KAFKA_BROKER="bitnami-kafka-0.bitnami-kafka-headless.uc0.svc.cluster.local:9092"
ENV KAFKA_TOPIC="temperature-readings"
ENV START_VALUE="1.0"
ENV END_VALUE="99.99"
ENV VALUE_TYPE="float"
ENV INVALID_VALUE_OCCURRENCE="100"
ENV INVALID_VALUE="200.0"
ENV MIN_THRESHOLD_VALUE="10.0"
ENV MAX_THRESHOLD_VALUE="90.0"
ENV SAVE_DATA="file"

ARG Pathdir="/mqtt"

RUN mkdir $Pathdir
RUN mkdir /data

COPY generator/generator.py $Pathdir
COPY actuator/temp-actuator.py $Pathdir
COPY analyzer/temp-analyzer.py $Pathdir
COPY publisher/publisher.py $Pathdir
COPY subscriber/subscriber.py $Pathdir
COPY load-testing/disk-load.sh $Pathdir

COPY requirements.txt .

#RUN apk update && apk add build-essential
#RUN /usr/local/bin/python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt

WORKDIR $Pathdir

#RUN chmod +x load-testing/disk-load.sh

#ENTRYPOINT ["python3", "actuate.py"]