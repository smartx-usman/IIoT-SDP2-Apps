#!/usr/bin/env python3
import logging
import os
import sys
import time

import faust
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from paho.mqtt import client as mqtt_client

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.WARN)

mqtt_broker = os.environ['MQTT_BROKER']
mqtt_port = int(os.environ['MQTT_BROKER_PORT'])
mqtt_topic = os.environ['MQTT_ACTUATOR_TOPIC']
mqtt_client_id = f'mqtt-faust-analyzer'
kafka_broker = 'kafka://' + os.environ['KAFKA_BROKER']
kafka_topic = os.environ['KAFKA_TOPIC']
kafka_key = "server-room"
value_type = os.environ['VALUE_TYPE']
save_data = os.environ['SAVE_DATA']
data_file_normal = "/analyzer/temperature-data-normal.csv"
data_file_anomalous = "/analyzer/temperature-data-anomalous.csv"
actuator_id = 'actuator-0'
actuator_actions = ['power-on', 'pause', 'shutdown']


def connect_to_cassandra():
    """Create Cassandra connection"""
    auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
    cluster = Cluster(['cassandra-0.cassandra-headless.uc2.svc.cluster.local'],
                      auth_provider=auth_provider)

    try:
        session = cluster.connect()
    except Exception as ex:
        logging.error(f'Problem while connecting to Casandra.')

    try:
        session.execute(f'DROP keyspace IF EXISTS iiot;')
        logging.info("Creating keyspace...")
        session.execute(
            "create keyspace iiot with replication={'class': 'SimpleStrategy', 'replication_factor' : 1};")
        logging.info(f'Created keyspace iiot.')
    except Exception as ex:
        logging.error(f'Problem while dropping or creating iiot keyspace.')

    try:
        session = cluster.connect('iiot')
    except Exception as ex:
        logging.error(f'Problem while connecting to Casandra.')

    query_temperature_valid_table = '''
    create table temperature (
       readingTS timestamp,
       processTS timestamp,
       sensorID text,
       readingValue float,
       primary key(readingTS)
    );'''
    query_temperature_invalid_table = '''
    create table temperature_invalid (
       readingTS timestamp,
       processTS timestamp,
       sensorID text,
       readingValue float,
       primary key(readingTS)
    );'''

    try:
        session.execute(query_temperature_valid_table)
    except Exception as ex:
        logging.info(f'Table already exists. Not creating.')

    try:
        session.execute(query_temperature_invalid_table)
    except Exception as ex:
        logging.info(f'Table already exists. Not creating.')

    return session


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
if save_data == 'file':
    if os.path.exists(data_file_normal):
        os.remove(data_file_normal)
        logging.info('Removed old file from the PV.')
    else:
        logging.info('The file does not exist.')

    if os.path.exists(data_file_anomalous):
        os.remove(data_file_anomalous)
        logging.info('Removed old file from the PV.')
    else:
        logging.info('The file does not exist.')

    # Open data file for writing
    try:
        temperature_file_normal = open(data_file_normal, "a")
    except Exception as ex:
        logging.error(f'Exception while opening file {temperature_file_normal}.', exc_info=True)

    try:
        temperature_file_anomalous = open(data_file_anomalous, "a")
    except Exception as ex:
        logging.error(f'Exception while opening file {temperature_file_anomalous}.', exc_info=True)

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

if save_data == 'cassandra':
    session = connect_to_cassandra()

app = faust.App('temp-analyzer', broker=kafka_broker, )
topic = app.topic(kafka_topic, value_type=Temperature)


# Create worker to process incoming streaming data
@app.agent(topic)
async def check(temperatures):
    async for temperature in temperatures:
        start_time = time.perf_counter()
        logging.info(f'Reading: {temperature.value} Timestamp: {temperature.reading_ts} Sensor: {temperature.sensor}')

        # Write data to a file
        #temperature_file.write(temperature.reading_ts + "," + temperature.sensor + "," + temperature.value + "\n")

        # ts = int(temperature.reading_ts[:-3])
        processts = int(time.time())
        readingts = int(temperature.reading_ts[:-3])
        # readingts = datetime.datetime.fromtimestamp(ts)

        # Create some checks on incoming data to create actuator actions
        if value_type == 'integer':
            if int(temperature.value) == invalid_value:
                if save_data == 'cassandra':
                    session.execute(
                        """
                        INSERT INTO temperature_invalid (readingTS, ProcessTS, sensorID, readingValue) VALUES(%s, %s, %s, %s)
                        """,
                        (readingts, processts, temperature.sensor, float(temperature.value))
                    )
                elif save_data == 'file':
                    temperature_file_anomalous.write(
                        str(readingts) + "," + str(processts) + "," + temperature.sensor + "," + temperature.value + "\n")
                logging.warning('Anomalous value found. It is discarded from further analysis.')
            else:
                if int(temperature.value) < min_threshold_value:
                    parse_message_for_actuator(temperature.reading_ts, actuator_id, actuator_actions[0])
                elif int(temperature.value) > max_threshold_value:
                    parse_message_for_actuator(temperature.reading_ts, actuator_id, actuator_actions[2])
                else:
                    logging.info('No action required.')

                if save_data == 'cassandra':
                    session.execute(
                        """
                        INSERT INTO temperature (readingTS, ProcessTS, sensorID, readingValue) VALUES(%s, %s, %s, %s)
                        """,
                        (readingts, processts, temperature.sensor, int(temperature.value))
                    )
                elif save_data == 'file':
                    temperature_file_normal.write(
                        str(readingts) + "," + str(processts) + "," + temperature.sensor + "," + temperature.value + "\n")
        elif value_type == 'float':
            if float(temperature.value) == invalid_value:
                if save_data == 'cassandra':
                    session.execute(
                        """
                        INSERT INTO temperature_invalid (readingTS, ProcessTS, sensorID, readingValue) VALUES(%s, %s, %s, %s)
                        """,
                        (readingts, processts, temperature.sensor, float(temperature.value))
                    )
                elif save_data == 'file':
                    temperature_file_anomalous.write(
                        str(readingts) + "," + str(processts) + "," + temperature.sensor + "," + temperature.value + "\n")

                logging.warning('Anomalous value found. It is discarded from further analysis.')
            else:
                if float(temperature.value) < min_threshold_value:
                    parse_message_for_actuator(temperature.reading_ts, actuator_id, actuator_actions[0])
                elif float(temperature.value) > max_threshold_value:
                    parse_message_for_actuator(temperature.reading_ts, actuator_id, actuator_actions[2])
                else:
                    logging.info('No action required.')

                if save_data == 'cassandra':
                    session.execute(
                        """
                        INSERT INTO temperature (readingTS, ProcessTS, sensorID, readingValue) VALUES(%s, %s, %s, %s)
                        """,
                        (readingts, processts, temperature.sensor, float(temperature.value))
                    )
                elif save_data == 'file':
                    temperature_file_normal.write(
                        str(readingts) + "," + str(processts) + "," + temperature.sensor + "," + temperature.value + "\n")

        end_time = time.perf_counter()
        time_ms = (end_time - start_time) * 1000
        logging.info(f'Message processing took {time_ms} ms.')


if __name__ == '__main__':
    app.main()
