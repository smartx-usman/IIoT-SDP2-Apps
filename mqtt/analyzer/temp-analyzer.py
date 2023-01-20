"""
For generating synthetic data.
Version: 0.5.1
"""

import logging
import os
import sys
import time

import faust
from faust import Record
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

from paho.mqtt import client as mqtt_client

from cassandra_store import CassandraStore
from file_store import FileStore
from mysql_store import MySQLStore

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

mqtt_broker = os.environ['MQTT_BROKER']
mqtt_port = int(os.environ['MQTT_BROKER_PORT'])
mqtt_topic = os.environ['MQTT_ACTUATOR_TOPIC']
mqtt_client_id = f'mqtt-faust-analyzer'
kafka_broker = 'kafka://' + os.environ['KAFKA_BROKER']
kafka_topic = os.environ['KAFKA_TOPIC']
kafka_key = "server-room"
save_data = os.environ['SAVE_DATA']
database_url = os.environ['DATABASE_URL']
jaeger_agent_host = os.environ['JAEGER_AGENT_HOST']
jaeger_agent_port = int(os.environ['JAEGER_AGENT_PORT'])
trace_sampling_rate = int(os.environ['TRACE_SAMPLING_RATE'])
data_file_normal = "/analyzer/temperature-data-normal.csv"
data_file_anomalous = "/analyzer/temperature-data-anomalous.csv"
actuator_id = 'actuator-0'
actuator_actions = ['power-on', 'pause', 'shutdown']

logging.info('MQTT Broker: %s', mqtt_broker)
logging.info('MQTT Port: %s', mqtt_port)
logging.info('MQTT Topic: %s', mqtt_topic)
logging.info('Kafka Broker: %s', kafka_broker)
logging.info('Kafka Topic: %s', kafka_topic)
logging.info('Database URL: %s', database_url)
logging.info('Trace sampling rate: %s', trace_sampling_rate)

resource = Resource(attributes={
    SERVICE_NAME: "temp-analyzer-processor"
})

jaeger_exporter = JaegerExporter(
    agent_host_name=jaeger_agent_host,
    agent_port=jaeger_agent_port,
)

"""sample 1 in every n traces"""
sampler = TraceIdRatioBased(1 / trace_sampling_rate)

provider = TracerProvider(resource=resource, sampler=sampler)
processor = BatchSpanProcessor(jaeger_exporter)
provider.add_span_processor(processor)

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)


def connect_to_mqtt():
    """Connect to MQTT broker"""
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info('Message: Connected to MQTT Broker!')
        else:
            logging.critical(f'Message: Failed to connect, Code: {rc}.')
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
    with tracer.start_as_current_span("publisher") as child_level3_span1:
        time_ms = round(time.time() * 1000)
        message = f'processed_ts:{time_ms} {message}'
        result = mqtt_publisher.publish(mqtt_topic, message)
        status = result[0]

        if status == 0:
            pass
        else:
            logging.error(f"Message: Failed to send message, Status: {status}")


def parse_message_for_actuator(sensor, reading_ts, actuator, action):
    """Parse message for MQTT"""
    with tracer.start_as_current_span("parser") as child_level2_span1:
        message = f"reading_ts:{reading_ts} actuator_id:{actuator} sensor:{sensor} action:{action}"
        mqtt_publish_message(client, message)


def get_actuator_action(sensor, value, reading_ts):
    """Find action for the actuator"""
    with tracer.start_as_current_span("ruler") as child_level1_span1:
        if value < min_threshold_value:
            parse_message_for_actuator(sensor, reading_ts, actuator_id, actuator_actions[0])
        elif value > max_threshold_value:
            parse_message_for_actuator(sensor, reading_ts, actuator_id, actuator_actions[2])
        else:
            pass


with tracer.start_as_current_span("analyzer-setup") as parent_span_1:
    """Cast values to correct type"""
    min_threshold_value = int(os.environ['MIN_THRESHOLD_VALUE'])
    max_threshold_value = int(os.environ['MAX_THRESHOLD_VALUE'])
    valid_value_range_start = int(os.environ['VALID_VALUE_RANGE_START'])
    valid_value_range_end = int(os.environ['VALID_VALUE_RANGE_END'])

    with tracer.start_as_current_span("store-connector") as child_level1_span3:
        """Data storage connection setup"""
        if save_data == 'cassandra':
            table_valid = 'temperature'
            table_invalid = 'temperature_invalid'
            with tracer.start_as_current_span("store-connector") as child_level1_span4:
                child_level1_span4.set_attribute('store_name', save_data)
                store = CassandraStore(database_url=database_url)
        elif save_data == 'mysql':
            table_valid = 'temperature'
            table_invalid = 'temperature_invalid'
            with tracer.start_as_current_span("store-connector") as child_level1_span4:
                child_level1_span4.set_attribute('store_name', save_data)
                store = MySQLStore(database_url=database_url)
        elif save_data == 'file':
            with tracer.start_as_current_span("store-connector") as child_level1_span4:
                child_level1_span4.set_attribute('store_name', save_data)
                store = FileStore()
                file_valid, file_invalid = store.open_file(data_file_normal=data_file_normal,
                                                           data_file_anomalous=data_file_anomalous)
            table_valid = file_valid
            table_invalid = file_invalid
        else:
            logging.info('Message: Data is not going to be saved.')

    with tracer.start_as_current_span("type-setter") as child_level1_span5:
        """Create a class to parse messages from Kafka"""
        class Temperature(Record, serializer='json'):
            measurement_ts: str
            sensor: str
            temperature: int
            humidity: float

    with tracer.start_as_current_span("type-setter") as child_level1_span6:
        client = connect_to_mqtt()

    with tracer.start_as_current_span("faust-connector") as child_level1_span7:
        app = faust.App('temp-analyzer', broker=kafka_broker, value_serializer='json')
        topic = app.topic(kafka_topic, value_type=Temperature)


@app.agent(topic)
async def process_data(messages):
    async for message in messages:
        with tracer.start_as_current_span("analyzer") as parent_span:
            """Create worker to process incoming streaming data"""
            start_time = time.perf_counter()
            process_ts = int(time.time())
            temperature_value = int(message.temperature)
            humidity_value = float(message.humidity)
            reading_ts = int(str(message.measurement_ts)[:-3])

            """Create some checks on incoming data to create actuator actions"""
            if valid_value_range_start <= temperature_value >= valid_value_range_end:
                with tracer.start_as_current_span("store") as child_level1_span2:
                    child_level1_span2.set_attribute('store_name', save_data)
                    store.store_data(table=table_invalid, reading_ts=reading_ts, process_ts=process_ts,
                                     sensor=message.sensor, temperature=temperature_value, humidity=humidity_value)
                logging.warning(f'Message: Anomalous data value, Sensor: {message.sensor}, Value: {str(temperature_value)}')
            else:
                get_actuator_action(sensor=message.sensor, value=temperature_value,
                                    reading_ts=reading_ts)

                with tracer.start_as_current_span("store") as child_level1_span2:
                    child_level1_span2.set_attribute('store_name', save_data)
                    store.store_data(table=table_valid, reading_ts=reading_ts, process_ts=process_ts,
                                     sensor=message.sensor, temperature=temperature_value, humidity=humidity_value)
                    logging.info(
                        f'Message: Normal data value, Sensor: {message.sensor}, Value: {str(temperature_value)}')

            end_time = time.perf_counter()
            time_ms = round((end_time - start_time) * 1000, 4)
            logging.info(f'Message: Total processing time, Sensor: {message.sensor}, Processing_time: {time_ms}ms')
            parent_span.set_attribute('sensor', message.sensor)
            parent_span.set_attribute('processing_time', time_ms)


if __name__ == '__main__':
    app.main()
