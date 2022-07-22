#!/usr/bin/env python3
"""
For publishing synthetic data to MQTT.
Author: Muhammad Usman
Version: 0.3.0
"""

import argparse as ap
import logging
import os
import sys
import time
from threading import Thread

import numpy as np
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
    parser.add_argument('-dt', '--delay_type', nargs=1, help='Message delay type fixed|random', required=True)
    parser.add_argument('-dsar', '--delay_start_range', nargs=1, help='Message delay start range', required=False)
    parser.add_argument('-dstr', '--delay_end_range', nargs=1, help='Message delay stop range', required=False)
    parser.add_argument('-de', '--delay', nargs=1, help='Message delay', required=False)

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
def connect_mqtt(client_id):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
        else:
            logging.critical("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(arguments.mqtt_broker[0], int(arguments.mqtt_broker_port[0]))
    return client


def value_type_normal(client, client_id, delay):
    # Check delay type
    if len(delay) == 1:
        msg_count = 1
        while True:
            start_time = time.perf_counter()
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
                    time.sleep(delay[0])

            end_time = time.perf_counter()
            logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete one iteration.')
    else:
        msg_count = 1
        while True:
            start_time = time.perf_counter()
            delay_index = 0
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
                    time.sleep(delay[delay_index])

                    delay_index = delay_index + 1
                    if delay_index == len(delay):
                        delay_index = 0

            end_time = time.perf_counter()
            logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete one iteration.')


def value_type_abnormal(client, client_id, delay):
    # Check delay type
    if len(delay) == 1:
        msg_count = 1
        while True:
            start_time = time.perf_counter()

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
                    time.sleep(delay[0])

            end_time = time.perf_counter()
            logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete one iteration.')
    else:
        msg_count = 1
        while True:
            start_time = time.perf_counter()
            delay_index = 0
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
                    time.sleep(delay[delay_index])

                    delay_index = delay_index + 1
                    if delay_index == len(delay):
                        delay_index = 0

            end_time = time.perf_counter()
            logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete one iteration.')


def value_type_both(client, client_id, delay):
    # Check delay type
    if len(delay) == 1:
        msg_count = 1
        while True:
            start_time = time.perf_counter()
            with open(f'/data/{arguments.normal_input_file[0]}') as fp_normal:
                values = fp_normal.readlines()
                with open(f'/data/{arguments.abnormal_input_file[0]}') as fp_abnormal:
                    abnormal_values = fp_abnormal.readlines()

                current_value_index = 0
                count = 1

                for value in values:
                    if count == int(arguments.invalid_value_occurrence[0]):
                        # for abnormal_value in abnormal_values:
                        value = abnormal_values[current_value_index]
                        # value = arguments.invalid_value[0]
                        current_value_index = current_value_index + 1
                        count = 0

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
                    time.sleep(delay[0])
            end_time = time.perf_counter()
            logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete one iteration.')
    else:
        msg_count = 1
        while True:
            start_time = time.perf_counter()
            delay_index = 0
            with open(f'/data/{arguments.normal_input_file[0]}') as fp_normal:
                values = fp_normal.readlines()
                with open(f'/data/{arguments.abnormal_input_file[0]}') as fp_abnormal:
                    abnormal_values = fp_abnormal.readlines()

                current_value_index = 0
                count = 1

                for value in values:
                    if count == int(arguments.invalid_value_occurrence[0]):
                        # for abnormal_value in abnormal_values:
                        value = abnormal_values[current_value_index]
                        # value = arguments.invalid_value[0]
                        current_value_index = current_value_index + 1
                        count = 0

                    time_ms = round(time.time() * 1000)
                    msg = f"measurement_ts: {time_ms} client_id: {client_id} msg_count: {msg_count} value: {str(value).strip()}"
                    result = client.publish(arguments.mqtt_topic[0], msg)
                    status = result[0]

                    if status == 0:
                        logging.info(f"Send `{msg}` to topic `{arguments.mqtt_topic[0]}`")
                    else:
                        logging.error(f"Failed to send message to topic {arguments.mqtt_topic[0]}")

                    time.sleep(delay[delay_index])
                    count += 1
                    msg_count += 1
                    delay_index += 1
                    if delay_index == len(delay):
                        delay_index = 0
            end_time = time.perf_counter()
            logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete one iteration.')


def fixed_delay(client, client_id):
    delay = [float(arguments.delay[0])]

    # Check value type
    if arguments.value_type[0] == 'normal':
        value_type_normal(client, client_id, delay)
    elif arguments.value_type[0] == 'abnormal':
        value_type_abnormal(client, client_id, delay)
    elif arguments.value_type[0] == 'both':
        value_type_both(client, client_id, delay)
    else:
        logging.error(f'Invalid data value_type is provided: {arguments.value_type[0]}')
        sys.exit(1)


def random_delay(client, client_id):
    delay = list(np.random.uniform(low=float(arguments.delay_start_range[0]),
                                   high=float(arguments.delay_end_range[0]),
                                   size=int(10)))

    # Check value type
    if arguments.value_type[0] == 'normal':
        value_type_normal(client, client_id, delay)
    elif arguments.value_type[0] == 'abnormal':
        value_type_abnormal(client, client_id, delay)
    elif arguments.value_type[0] == 'both':
        value_type_both(client, client_id, delay)
    else:
        logging.error(f'Invalid data value_type is provided: {arguments.value_type[0]}')
        sys.exit(1)


# Publish message to MQTT topic
def mqtt_publish_message(client_id):
    client = connect_mqtt(client_id)
    client.loop_start()

    # Check delay type
    if arguments.delay_type[0] == 'fixed':
        fixed_delay(client=client, client_id=client_id)
    elif arguments.delay_type[0] == 'random':
        random_delay(client=client, client_id=client_id)
    else:
        logging.error(f'Invalid message delay_type is provided: {arguments.delay_type[0]}')
        sys.exit(1)


def run():
    try:
        threads = []
        sensor_count = int(arguments.sensors[0])

        logging.info(f'Number of sensors to start {sensor_count}.')

        for n in range(0, sensor_count):
            t = Thread(target=mqtt_publish_message, args=(f"{pod_name}-{n}",))
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
