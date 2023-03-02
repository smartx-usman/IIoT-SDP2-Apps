# python3.6
import logging
import os
import time

from paho.mqtt import client as mqtt_client
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

resource = Resource(attributes={
    SERVICE_NAME: "mqtt-microservice"
})

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger-agent.observability.svc.cluster.local",
    agent_port=6831,
)

provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(jaeger_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

mqtt_broker = os.environ['MQTT_BROKER']
mqtt_port = int(os.environ['MQTT_BROKER_PORT'])
mqtt_topic = os.environ['MQTT_ACTUATOR_TOPIC']
clientID = f'python-mqtt-actuator'


# Connect to MQTT broker
def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info('message=Connected to MQTT Broker!')
        else:
            logging.critical(f'message=Failed to connect, return code {rc}.')

    try:
        client = mqtt_client.Client(clientID)
        client.on_connect = on_connect
        client.connect(mqtt_broker, mqtt_port)
    except Exception as ex:
        logging.critical('message=Exception while connecting MQTT.', exc_info=True)
    return client


# Subscribe messages from MQTT topic
def mqtt_subscribe_message(client: mqtt_client):
    def on_message(client, userdata, msg):
        time_ms = round(time.time() * 1000)
        message = msg.payload.decode()
        logging.info(f'message=Message details, current_ts:{time_ms}, {message}')
        split_message = message.split()
        reading_ts = int((split_message[1].split(':'))[1])
        total_delay = (time_ms - reading_ts)

        # logging.info(f'[Processor] {split_message[3]} is going to be processed by {split_message[3]}')
        logging.info(f'message=End-to-end delay (reading_ts - current_ts), value={total_delay}ms')
        #    parent_span.set_attribute('e2e_latency', total_delay)

    client.subscribe(mqtt_topic)
    client.on_message = on_message


def run():
    mqtt_subscriber = connect_mqtt()
    mqtt_subscribe_message(mqtt_subscriber)
    mqtt_subscriber.loop_forever()


if __name__ == '__main__':
    run()
