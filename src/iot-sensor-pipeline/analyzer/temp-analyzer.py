import json
import logging
import os

from confluent_kafka import Consumer, KafkaError

from action_generator import ActionGenerator
from message_processor import process_message
from mqtt_publisher import MQTTPublish
from store_factory import get_store
from tracing_setup import setup_tracer

"""Configure logging"""
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

"""Environment configuration"""
kafka_broker = f"{os.environ['KAFKA_BROKER']}.{os.environ['POD_NAMESPACE']}.svc.cluster.local:9092"
kafka_topic = os.environ['KAFKA_TOPIC']
database_url = f"{os.environ['DATABASE_URL']}.{os.environ['POD_NAMESPACE']}.svc.cluster.local"
datastore = os.environ['DATASTORE']
trace_agent_host = os.environ['TRACE_AGENT_HOST']
trace_agent_port = os.environ['TRACE_AGENT_PORT']
trace_sampling_rate = int(os.environ['TRACE_SAMPLING_RATE'])
valid_value_range_start = int(os.environ['VALID_VALUE_RANGE_START'])
valid_value_range_end = int(os.environ['VALID_VALUE_RANGE_END'])
data_file_normal = "/analyzer/temperature-data-normal.csv"
data_file_anomalous = "/analyzer/temperature-data-anomalous.csv"

logging.info('Kafka Broker: %s', kafka_broker)
logging.info('Kafka Topic: %s', kafka_topic)
logging.info('Database URL: %s', database_url)
logging.info('Trace sampling rate: %s', trace_sampling_rate)

"""Setup tracing"""
tracer = setup_tracer("weather-analyzer", trace_agent_host, trace_agent_port, trace_sampling_rate)

with tracer.start_as_current_span("analyzer-setup") as parent_span_1:
    """Cast values to correct type"""
    valid_value_range_start = int(os.environ['VALID_VALUE_RANGE_START'])
    valid_value_range_end = int(os.environ['VALID_VALUE_RANGE_END'])

    with tracer.start_as_current_span("store-finder") as child_level1_span3:
        """Data storage connection setup"""
        # Setup store
        store, table_valid, table_invalid = get_store(
            datastore=datastore,
            database_url=database_url,
            data_file_normal=data_file_normal,
            data_file_anomalous=data_file_anomalous,
            tracer=tracer
        )

    """Setup MQTT and action generator"""
    mqtt_client = MQTTPublish(tracer=tracer)
    action_generator = ActionGenerator(tracer=tracer, mqtt_client=mqtt_client)


def create_consumer():
    return Consumer({
        'bootstrap.servers': kafka_broker,
        'group.id': 'weather-analyzer-group',
        'auto.offset.reset': 'earliest'
    })


def consume_messages():
    logging.info('Creating Kafka consumer...')
    consumer = create_consumer()
    consumer.subscribe([kafka_topic])
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logging.info('End of partition reached %s [%d] at offset %d', msg.topic(), msg.partition(),
                                 msg.offset())
                else:
                    logging.error(msg.error())
                    break
            else:
                message_value = json.loads(msg.value().decode('utf-8'))
                process_message(
                    message=message_value,
                    store=store,
                    tracer=tracer,
                    action_generator=action_generator,
                    table_valid=table_valid,
                    table_invalid=table_invalid,
                    datastore=datastore,
                    valid_range=(valid_value_range_start, valid_value_range_end)
                )
    finally:
        consumer.close()


if __name__ == '__main__':
    logging.info('Starting temperature analyzer...')
    consume_messages()
