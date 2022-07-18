#!/usr/bin/env python3
"""
For publishing synthetic data to MQTT.
Author: Muhammad Usman
Version: 0.2.0
"""

import argparse as ap
import logging
import os
import sys
import time
from threading import Thread

from paho.mqtt import client as mqtt_client

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def parse_arguments():
    """Read and parse commandline arguments"""
    parser = ap.ArgumentParser(prog='data_generator', usage='%(prog)s [options]', add_help=True)
    parser.add_argument('-t', '--value_type', nargs=1, help='Value type normal|abnormal|both', required=True)
    parser.add_argument('-d', '--data_type', nargs=1, help='Data type integer|float|both', required=True)

    parser.add_argument('-m', '--mqtt_broker', nargs=1, help='MQTT broker ip or service name', required=True)
    parser.add_argument('-p', '--mqtt_broker_port', nargs=1, help='MQTT broker port', required=True)
    parser.add_argument('-to', '--mqtt_topic', nargs=1, help='MQTT broker topic', required=True)

    parser.add_argument('-s', '--sensors', nargs=1, help='The number of sensors to start', required=True)
    parser.add_argument('-de', '--delay', nargs=1, help='Message delay', required=True)

    parser.add_argument('-io', '--invalid_value_occurrence', nargs=1, help='Invalid value occurrence position',
                        required=False)
    parser.add_argument('-iv', '--invalid_value', nargs=1, help='Invalid value', required=False)

    parser.add_argument('-ni', '--normal_input_file', nargs=1, help='Normal data input file name', required=True)
    parser.add_argument('-ai', '--abnormal_input_file', nargs=1, help='Abnormal data input file name', required=False)

    return parser.parse_args(sys.argv[1:])


# topic = "mqtt/temperature"
# username = 'emqx'
# password = 'public'


# Connect to MQTT broker
def connect_mqtt(clientID):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
        else:
            logging.critical("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(clientID)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(arguments.mqtt_broker[0], int(arguments.mqtt_broker_port[0]))
    return client


# Publish message to MQTT topic
def mqtt_publish_message(client_id, delay):
    msg_count = 1
    client = connect_mqtt(client_id)
    client.loop_start()

    while True:
        start_time = time.perf_counter()
        if arguments.value_type[0] == 'normal':
            with open(f'/data/{arguments.normal_input_file[0]}') as fp:
                values = fp.readlines()
                for value in values:
                    time_ms = round(time.time() * 1000)
                    msg = f"measurement_ts: {time_ms} client_id: {client_id} msg_count: {msg_count} value: {str(value).strip()}"
                    result = client.publish(arguments.mqtt_topic[0], msg)
                    status = result[0]

                    if status == 0:
                        logging.info(f"Send `{msg}` to topic `{arguments.mqtt_topic[0]}`")
                    else:
                        logging.error(f"Failed to send message to topic {arguments.mqtt_topic[0]}")

                    msg_count += 1
                    time.sleep(delay)
        elif arguments.value_type[0] == 'abnormal':
            with open(f'/data/{arguments.abnormal_input_file[0]}') as fp:
                values = fp.readlines()
                for value in values:
                    time_ms = round(time.time() * 1000)
                    msg = f"measurement_ts: {time_ms} client_id: {client_id} msg_count: {msg_count} value: {str(value).strip()}"
                    result = client.publish(arguments.mqtt_topic[0], msg)
                    status = result[0]

                    if status == 0:
                        logging.info(f"Send `{msg}` to topic `{arguments.mqtt_topic[0]}`")
                    else:
                        logging.error(f"Failed to send message to topic {arguments.mqtt_topic[0]}")

                    msg_count += 1
                    time.sleep(delay)
        else:
            with open(f'/data/{arguments.normal_input_file[0]}') as fp:
                values = fp.readlines()
                for value in values:
                    if count == arguments.invalid_value_occurrence[0]:
                        value = arguments.invalid_value[0]
                        count = 1

                    time_ms = round(time.time() * 1000)
                    msg = f"measurement_ts: {time_ms} client_id: {client_id} msg_count: {msg_count} value: {str(value).strip()}"
                    result = client.publish(arguments.mqtt_topic[0], msg)
                    status = result[0]

                    if status == 0:
                        logging.info(f"Send `{msg}` to topic `{arguments.mqtt_topic[0]}`")
                    else:
                        logging.error(f"Failed to send message to topic {arguments.mqtt_topic[0]}")

                    count += 1
                    msg_count += 1
                    time.sleep(delay)

        end_time = time.perf_counter()
        logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete.')


def run():
    try:
        threads = []
        sensor_count = int(arguments.sensors[0])
        delay = float(arguments.delay[0])
        logging.info(f'Number of sensors to start {sensor_count} with delay {delay}.')

        for n in range(0, sensor_count):
            t = Thread(target=mqtt_publish_message, args=(f"{pod_name}-{n}", delay,))
            threads.append(t)
            t.start()

        # wait for the threads to complete
        for t in threads:
            t.join()
    except Exception as e:
        logging.error("Unable to start thread", exc_info=True)


arguments = parse_arguments()
pod_name = os.environ['POD_NAME']

# Cast values from string to integer
if arguments.data_type[0] == 'integer':
    invalid_value = int(os.environ['INVALID_VALUE'])
    invalid_value = str(invalid_value) + ',' + str(float(invalid_value))

# Cast values from string to float
if arguments.data_type[0] == 'float':
    invalid_value = float(os.environ['INVALID_VALUE'])
    invalid_value = str(int(invalid_value)) + ',' + str(invalid_value)

run()
