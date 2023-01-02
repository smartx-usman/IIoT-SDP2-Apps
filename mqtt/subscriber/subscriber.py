import json
import logging
import os
import random

from kafka import KafkaProducer
from paho.mqtt import client as mqtt_client

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

mqtt_broker = os.environ['MQTT_BROKER']
mqtt_port = int(os.environ['MQTT_BROKER_PORT'])
mqtt_topic = os.environ['MQTT_TOPIC']
thingsboard_device_token = os.environ['THINGSBOARD_DEVICE_TOKEN']
kafka_broker = os.environ['KAFKA_BROKER']
kafka_topic = os.environ['KAFKA_TOPIC']
kafka_key = "server-room"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'


def connect_mqtt() -> mqtt_client:
    """Connect to MQTT broker"""
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info('Connected to MQTT Broker!')
        else:
            logging.critical(f'Failed to connect, return code {rc}.')

    try:
        client = mqtt_client.Client(client_id)
        client.username_pw_set(thingsboard_device_token)
        client.on_connect = on_connect
        client.connect(mqtt_broker, mqtt_port)
    except Exception as ex:
        logging.critical('Exception while connecting MQTT.', exc_info=True)
    return client


def connect_kafka_producer(kafka_broker):
    """Creates a Kafka producer"""
    _producer = None
    try:
        _producer = KafkaProducer(bootstrap_servers=kafka_broker, api_version=(1, 0, 0))
    except Exception as ex:
        logging.critical('Exception while connecting Kafka.', exc_info=True)
    return _producer


def kafka_publish_message(producer_instance, message):
    """Publish message to Kafka topic"""
    try:
        key_bytes = bytes(kafka_key, encoding='utf-8')
        split_message = message.split()
        json_message = {
            'reading_ts': split_message[1],
            'sensor': split_message[3],
            'value': split_message[5]
        }

        message_dump = json.dumps(json_message)
        value_bytes = bytes(message_dump, encoding='utf-8')
        producer_instance.send(kafka_topic, key=key_bytes, value=value_bytes)
        producer_instance.flush()
        #logging.info('Message published successfully.')
    except Exception as ex:
        logging.error('Exception in publishing message.', exc_info=True)


def mqtt_subscribe_message(client: mqtt_client, producer):
    """Subscribe to MQTT topic"""
    def on_message(client, userdata, msg):
        logging.debug(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        message = msg.payload.decode()
        kafka_publish_message(producer, message)

    client.subscribe(mqtt_topic)
    client.on_message = on_message


def run():
    """Run the subscriber"""
    mqtt_subscriber = connect_mqtt()
    kafka_producer = connect_kafka_producer(kafka_broker)
    mqtt_subscribe_message(mqtt_subscriber, kafka_producer)
    mqtt_subscriber.loop_forever()


if __name__ == '__main__':
    run()
