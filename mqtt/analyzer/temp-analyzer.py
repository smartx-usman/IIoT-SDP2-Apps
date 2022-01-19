#!/usr/bin/env python3
import logging
import os
import sys
import time

import faust
from paho.mqtt import client as mqtt_client

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

mqtt_broker = os.environ['MQTT_BROKER']
mqtt_port = int(os.environ['MQTT_BROKER_PORT'])
mqtt_topic = os.environ['MQTT_ACTUATOR_TOPIC']
mqtt_client_id = f'mqtt-faust-analyzer'
kafka_broker = 'kafka://' + os.environ['KAFKA_BROKER']
kafka_topic = os.environ['KAFKA_TOPIC']
kafka_key = "server-room"
value_type = os.environ['VALUE_TYPE']
data_file_name = "/analyzer/temperature-data.csv"
actuator_id = 'actuator-0'
actuator_actions = ['power-on', 'pause', 'shutdown']


# Cast values to correct type
if value_type == 'integer':
    min_threshold_value = int(os.environ['MIN_THRESHOLD_VALUE'])
    max_threshold_value = int(os.environ['MAX_THRESHOLD_VALUE'])
    invalid_value = int(os.environ['INVALID_VALUE'])
elif value_type == 'float':
    min_threshold_value = float(os.environ['MIN_THRESHOLD_VALUE'])
    max_threshold_value = float(os.environ['MAX_THRESHOLD_VALUE'])
    invalid_value = float(os.environ['INVALID_VALUE'])


# Remove old data file from persistent volume
if os.path.exists(data_file_name):
    os.remove(data_file_name)
    logging.info('Removed old file from the PV.')
else:
    logging.info('The file does not exist.')

# Open data file for writing
try:
    temperature_file = open(data_file_name, "a")
except Exception as ex:
    logging.error(f'Exception while opening file {temperature_file}.', exc_info=True)

# Connect to MQTT broker
def connect_to_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info('Connected to MQTT Broker!')
        else:
            logging.critical(f'Failed to connect, return code {rc}.')

    try:
        client = mqtt_client.Client(mqtt_client_id)
        client.on_connect = on_connect
        client.connect(mqtt_broker, mqtt_port)
    except Exception as ex:
        logging.critical('Exception while connecting MQTT.', exc_info=True)
    return client


# Publish message to MQTT topic
def mqtt_publish_message(mqtt_publisher, message):
    time_ms = round(time.time() * 1000)
    message = f'processed_ts:{time_ms} {message}'
    result = mqtt_publisher.publish(mqtt_topic, message)
    status = result[0]

    if status == 0:
        logging.info(f"Send {message} to topic `{mqtt_topic}`")
    else:
        logging.error(f"Failed to send message to topic {mqtt_topic}")


client = connect_to_mqtt()


# Parse message for MQTT
def parse_message_for_actuator(reading_ts, actuator, action):
    logging.info(f'{action} heating system action is generated.')
    message = f"reading_ts:{reading_ts} actuator_id:{actuator} action:{action}"
    mqtt_publish_message(client, message)


# Create a class to parse message from Kafka
if value_type == 'integer':
    class Temperature(faust.Record, serializer='json'):
        reading_ts: int
        sensor: str
        value: int
elif value_type == 'float':
    class Temperature(faust.Record, serializer='json'):
        reading_ts: int
        sensor: str
        value: float
else:
    logging.critical(f'Invalid value type {value_type} is provided. Exiting.')
    sys.exit()

app = faust.App('temp-analyzer', broker=kafka_broker, )
topic = app.topic(kafka_topic, value_type=Temperature)


# Create worker to process incoming streaming data
@app.agent(topic)
async def check(temperatures):
    async for temperature in temperatures:
        start_time = time.perf_counter()
        logging.info(f'Reading: {temperature.value} Timestamp: {temperature.reading_ts} Sensor: {temperature.sensor}')

        # Write data to a file
        temperature_file.write(temperature.reading_ts + "," + temperature.sensor + "," + temperature.value + "\n")

        # Create some checks on incoming data to create actuator actions
        if value_type == 'integer':
            if int(temperature.value) == invalid_value:
                logging.warning('Anomalous value found. Value is discarded.')
            else:
                if int(temperature.value) < min_threshold_value:
                    parse_message_for_actuator(temperature.reading_ts, actuator_id, actuator_actions[0])
                elif int(temperature.value) > max_threshold_value:
                    parse_message_for_actuator(temperature.reading_ts, actuator_id, actuator_actions[2])
                else:
                    logging.info('No action required.')
        elif value_type == 'float':
            if float(temperature.value) == invalid_value:
                logging.warning('Anomalous value found. Value is discarded.')
            else:
                if float(temperature.value) < min_threshold_value:
                    parse_message_for_actuator(temperature.reading_ts, actuator_id, actuator_actions[0])
                elif float(temperature.value) > max_threshold_value:
                    parse_message_for_actuator(temperature.reading_ts, actuator_id, actuator_actions[2])
                else:
                    logging.info('No action required.')

        end_time = time.perf_counter()
        time_ms = (end_time - start_time) * 1000
        logging.info(f'Message processing took {time_ms} ms.')


if __name__ == '__main__':
    app.main()
