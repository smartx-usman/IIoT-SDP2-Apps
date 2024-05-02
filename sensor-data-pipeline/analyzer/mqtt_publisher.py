"""
For generating synthetic data.
Version: 0.2.0
"""

import logging
import os
import sys
import time

import paho.mqtt.client as mqtt_client


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
                logging.info('message=Connected to MQTT Broker!')
            else:
                logging.critical(f'message=Failed to connect, code: {rc}.')

        try:
            unacked_publish = set()
            client = mqtt_client.Client(client_id=self.client_id, clean_session=True, transport="tcp",
                                        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
            client.enable_logger()
            client.user_data_set(unacked_publish)

            #client = mqtt_client.Client(self.client_id)
            client.on_connect = on_connect
            client.connect(self.broker, self.port)
        except Exception as ex:
            logging.critical('message=Exception while connecting to MQTT.', exc_info=True)
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
                logging.error(f"message=Failed to send message, status={status}")
