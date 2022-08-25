"""
For generating synthetic data.
Author: Muhammad Usman
Version: 0.3.0
"""

import logging
import os
import sys
import time

import faust
from paho.mqtt import client as mqtt_client

from cassandra_store import CassandraStore
from file_store import FileStore
from mysql_store import MySQLStore

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
database_url = os.environ['DATABASE_URL']
data_file_normal = "/analyzer/temperature-data-normal.csv"
data_file_anomalous = "/analyzer/temperature-data-anomalous.csv"
actuator_id = 'actuator-0'
actuator_actions = ['power-on', 'pause', 'shutdown']


def connect_to_mqtt():
    """Connect to MQTT broker"""
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
        sys.exit(1)
    return client


def mqtt_publish_message(mqtt_publisher, message):
    """Publish message to MQTT topic"""
    time_ms = round(time.time() * 1000)
    message = f'processed_ts:{time_ms} {message}'
    result = mqtt_publisher.publish(mqtt_topic, message)
    status = result[0]

    if status == 0:
        pass
    else:
        logging.error(f"Failed to send message to topic {mqtt_topic}")


def parse_message_for_actuator(reading_ts, actuator, action):
    """Parse message for MQTT"""
    logging.info(f'{action} heating system action is generated.')
    message = f"reading_ts:{reading_ts} actuator_id:{actuator} action:{action}"
    mqtt_publish_message(client, message)


def get_actuator_action(value, reading_ts):
    """Find action for the actuator"""
    if value < min_threshold_value:
        parse_message_for_actuator(reading_ts, actuator_id, actuator_actions[0])
    elif value > max_threshold_value:
        parse_message_for_actuator(reading_ts, actuator_id, actuator_actions[2])
    else:
        logging.info('No actuator action is required.')


# Cast values to correct type
if value_type == 'integer':
    min_threshold_value = int(os.environ['MIN_THRESHOLD_VALUE'])
    max_threshold_value = int(os.environ['MAX_THRESHOLD_VALUE'])
    invalid_value = int(os.environ['INVALID_VALUE'])
elif value_type == 'float':
    min_threshold_value = float(os.environ['MIN_THRESHOLD_VALUE'])
    max_threshold_value = float(os.environ['MAX_THRESHOLD_VALUE'])
    invalid_value = float(os.environ['INVALID_VALUE'])

# Data storage connection setup
if save_data == 'cassandra':
    table_valid = 'temperature'
    table_invalid = 'temperature_invalid'
    store = CassandraStore(database_url=database_url)
elif save_data == 'mysql':
    table_valid = 'temperature'
    table_invalid = 'temperature_invalid'
    store = MySQLStore(database_url=database_url)
elif save_data == 'file':
    store = FileStore()
    file_valid, file_invalid = store.open_file(data_file_normal=data_file_normal,
                                               data_file_anomalous=data_file_anomalous)
    table_valid = file_valid
    table_invalid = file_invalid
else:
    logging.info('Data is not going to be saved.')

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
    sys.exit(1)

client = connect_to_mqtt()
app = faust.App('temp-analyzer', broker=kafka_broker, )
topic = app.topic(kafka_topic, value_type=Temperature)


# Create worker to process incoming streaming data
@app.agent(topic)
async def check(temperatures):
    async for temperature in temperatures:
        start_time = time.perf_counter()
        data_value = temperature.value.split(',')
        process_ts = int(time.time())
        reading_ts = int(temperature.reading_ts[:-3])

        # Create some checks on incoming data to create actuator actions
        if value_type == 'integer':
            if int(data_value[0]) == invalid_value:
                store.store_data(table=table_invalid, reading_ts=reading_ts, process_ts=process_ts,
                                 sensor=temperature.sensor,
                                 value=int(data_value[1]))
                logging.warning('Anomalous value found. Discarded from further analysis.')
            else:
                get_actuator_action(int(data_value[0]), temperature.reading_ts)

                store.store_data(table=table_valid, reading_ts=reading_ts, process_ts=process_ts,
                                 sensor=temperature.sensor,
                                 value=int(data_value[1]))
        elif value_type == 'float':
            if float(data_value[1]) == invalid_value:
                store.store_data(table=table_invalid, reading_ts=reading_ts, process_ts=process_ts,
                                 sensor=temperature.sensor,
                                 value=float(data_value[1]))
                logging.warning('Anomalous value found. Discarded from further analysis.')
            else:
                get_actuator_action(float(data_value[0]), temperature.reading_ts)

                store.store_data(table=table_valid, reading_ts=reading_ts, process_ts=process_ts,
                                 sensor=temperature.sensor,
                                 value=float(data_value[1]))

        end_time = time.perf_counter()
        time_ms = (end_time - start_time) * 1000
        logging.info(f'Message processing took {time_ms} ms.')


if __name__ == '__main__':
    app.main()
