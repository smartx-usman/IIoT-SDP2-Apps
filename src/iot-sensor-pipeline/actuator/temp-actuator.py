import logging
import os
import time

import paho.mqtt.client as mqtt_client

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

mqtt_broker = os.environ['MQTT_BROKER']
mqtt_port = int(os.environ['MQTT_BROKER_PORT'])
mqtt_topic = os.environ['MQTT_ACTUATOR_TOPIC']
clientID = f'python-mqtt-actuator'


def connect_mqtt():# -> mqtt_client:
    """Connect to MQTT Broker"""

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            logging.info('message=Connected to MQTT Broker!')
        else:
            logging.critical(f'message=Failed to connect, return code {rc}.')

    try:
        client = mqtt_client.Client(client_id=clientID, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
        client.enable_logger()

        client.on_connect = on_connect
        client.connect(mqtt_broker, mqtt_port)
    except Exception as ex:
        logging.critical('message=Exception while connecting MQTT.', exc_info=True)
    return client


def mqtt_subscribe_message(client: mqtt_client):
    """Subscribe to MQTT topic and receive action messages"""

    def on_message(client, userdata, msg):
        time_ms = round(time.time() * 1000)
        message = msg.payload.decode()
        logging.info(f'message=Message details, current_ts:{time_ms}, {message}')
        split_message = message.split()
        reading_ts = int((split_message[1].split(':'))[1])
        total_delay = (time_ms - reading_ts)

        logging.info(f'message=End-to-end delay (reading_ts - current_ts), value={total_delay}ms')

    client.subscribe(mqtt_topic)
    client.on_message = on_message


def run():
    mqtt_subscriber = connect_mqtt()
    mqtt_subscribe_message(mqtt_subscriber)
    mqtt_subscriber.loop_forever()


if __name__ == '__main__':
    run()
