#!/usr/bin/env python3
"""
For subscribing synthetic data from MQTT.
Version: 0.3.1
"""
import json
import logging
import os
import random

import paho.mqtt.client as mqtt_client
from kafka import KafkaProducer
from kafka.errors import TopicAlreadyExistsError
from kafka.admin import KafkaAdminClient, NewTopic

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

mqtt_broker = os.environ['MQTT_BROKER']
mqtt_port = int(os.environ['MQTT_BROKER_PORT'])
mqtt_topic = os.environ['MQTT_TOPIC']
thingsboard_device_token = os.environ['THINGSBOARD_DEVICE_TOKEN']
kafka_broker = os.environ['KAFKA_BROKER']
kafka_topic = os.environ['KAFKA_TOPIC']
num_partitions = int(os.environ['KAFKA_NUM_PARTITIONS'])
replication_factor = int(os.environ['KAFKA_REPLICATION_FACTOR'])
kafka_key = "server-room"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'


def connect_mqtt():
    """Connect to MQTT broker"""
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            logging.info('message=Connected to MQTT Broker!')
        else:
            logging.critical(f'message=Failed to connect, Code: {rc}')

    try:
        client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
        client.enable_logger()

        # client.username_pw_set(thingsboard_device_token)
        client.on_connect = on_connect
        client.connect(mqtt_broker, mqtt_port)
    except Exception as ex:
        logging.critical('message=Exception while connecting MQTT.', exc_info=True)
    return client


def connect_kafka_producer(kafka_broker):
    """Creates a Kafka producer"""
    _producer = None
    try:
        _producer = KafkaProducer(bootstrap_servers=kafka_broker)
    except Exception as ex:
        logging.critical('message=Exception while connecting Kafka.', exc_info=True)
    return _producer


def create_kafka_topic():
    # Create a Kafka admin client
    admin_client = KafkaAdminClient(
        bootstrap_servers=kafka_broker,
        client_id='python-kafka-client'
    )

    # Define the topic
    topic = NewTopic(
        name=kafka_topic,
        num_partitions=num_partitions,
        replication_factor=replication_factor
    )

    # Check if the topic already exists
    existing_topics = admin_client.list_topics()
    if kafka_topic in existing_topics:
        logging.info(f'Topic {kafka_topic} already exists.')
    else:
        try:
            admin_client.create_topics(new_topics=[topic], validate_only=False)
            logging.info(f'Topic {kafka_topic} created successfully.')
        except TopicAlreadyExistsError:
            logging.info(f'Topic {kafka_topic} already exists.')


def kafka_publish_message(producer_instance, message):
    """Publish message to Kafka topic"""
    try:
        key_bytes = bytes(kafka_key, encoding='utf-8')
        split_message = message.split(',')
        json_message = {
            'measurement_ts': split_message[0].split(':')[1],
            'temperature': split_message[1].split(':')[1],
            'humidity': split_message[2].split(':')[1],
            'sensor': split_message[3].split(':')[1][:-1]
        }
        message_dump = json.dumps(json_message)
        logging.info(f"message={message_dump}")
        value_bytes = bytes(message_dump, encoding='utf-8')
        producer_instance.send(kafka_topic, key=key_bytes, value=value_bytes)
        producer_instance.flush()
    except Exception as ex:
        logging.error('message=Exception in publishing message.', exc_info=True)


def mqtt_subscribe_message(client: mqtt_client, producer):
    """Subscribe to MQTT topic"""
    def on_message(client, userdata, msg):
        message = msg.payload.decode()
        kafka_publish_message(producer, message)

    client.subscribe(mqtt_topic)
    client.on_message = on_message


def run():
    """Run the subscriber"""
    mqtt_subscriber = connect_mqtt()
    kafka_producer = connect_kafka_producer(kafka_broker)
    create_kafka_topic()
    mqtt_subscribe_message(mqtt_subscriber, kafka_producer)
    mqtt_subscriber.loop_forever()


if __name__ == '__main__':
    run()
