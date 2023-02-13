"""
For generating synthetic data.
Version: 0.1.0
"""

import logging
import os
import sys
import time

from paho.mqtt import client as mqtt_client


class MQTTPublish():
    def __init__(self, tracer):
        self.broker = os.environ['MQTT_BROKER']
        self.port = int(os.environ['MQTT_BROKER_PORT'])
        self.topic = os.environ['MQTT_ACTUATOR_TOPIC']
        self.client_id = f'mqtt-faust-analyzer'
        self.tracer = tracer
        self.client = self.init_connect()

    def init_connect(self):
        """Connect to MQTT broker"""
        logging.info('MQTT Broker: %s', self.broker)
        logging.info('MQTT Port: %s', self.port)
        logging.info('MQTT Topic: %s', self.topic)

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logging.info('Message: Connected to MQTT Broker!')
            else:
                logging.critical(f'Message: Failed to connect, Code: {rc}.')

        try:
            client = mqtt_client.Client(self.client_id)
            client.on_connect = on_connect
            client.connect(self.broker, self.port)
        except Exception as ex:
            logging.critical('Exception while connecting MQTT.', exc_info=True)
            sys.exit(1)
        return client

    def publish_message(self, message):
        """Publish message to MQTT topic"""
        with self.tracer.start_as_current_span("publisher") as child_level3_span1:
            time_ms = round(time.time() * 1000)
            message = f'processed_ts:{time_ms} {message}'
            result = self.client.publish(self.topic, message)
            status = result[0]

            if status == 0:
                pass
            else:
                logging.error(f"Message: Failed to send message, Status: {status}")
