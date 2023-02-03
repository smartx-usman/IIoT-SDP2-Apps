"""
For generating synthetic data.
Version: 0.6.0
"""

import logging
import os
import time

import faust
from faust import Record
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

from cassandra_store import CassandraStore
from file_store import FileStore
from mysql_store import MySQLStore
from mqtt_publisher import MQTTPublish
from action_generator import ActionGenerator

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

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

with tracer.start_as_current_span("analyzer-setup") as parent_span_1:
    """Cast values to correct type"""
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
    with tracer.start_as_current_span("publisher-connector") as child_level1_span6:
        mqtt_client = MQTTPublish(tracer=tracer)
    with tracer.start_as_current_span("action-initializer") as child_level1_span7:
        action_generator = ActionGenerator(tracer=tracer, mqtt_client=mqtt_client)
    with tracer.start_as_current_span("stream-connector") as child_level1_span8:
        app = faust.App('temp-analyzer', broker=kafka_broker, value_serializer='json')
        topic = app.topic(kafka_topic, value_type=Temperature)


@app.agent(topic)
async def process_data(messages):
    async for message in messages:
        with tracer.start_as_current_span("analyzer") as parent_span:
            """Create worker to process incoming streaming data"""
            try:
                start_time = time.perf_counter()
                trace_id = format(parent_span.get_span_context().trace_id, "032x")
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
                        logging.warning(
                            f'message=Anomalous data value, sensor={message.sensor}, value={str(temperature_value)}, trace_id={trace_id}')
                else:
                    action_generator.get_actuator_action(sensor=message.sensor, value=temperature_value, ts=reading_ts)
                    with tracer.start_as_current_span("store") as child_level1_span2:
                        child_level1_span2.set_attribute('store_name', save_data)
                        store.store_data(table=table_valid, reading_ts=reading_ts, process_ts=process_ts,
                                         sensor=message.sensor, temperature=temperature_value, humidity=humidity_value)
                        logging.info(
                            f'message=Normal data value, sensor={message.sensor}, value={str(temperature_value)}, trace_id={trace_id}')
            except Exception as ex:
                logging.error(f'message=Error processing message, sensor={message.sensor}, error={str(ex)}')
                # try:
                #     if save_data == 'mysql':
                #         logging.info('message=Trying to reconnect to MySQL database')
                #         store = MySQLStore.connect_db(database_url=database_url)
                # except Exception as ex:
                #     pass

            end_time = time.perf_counter()
            time_ms = round((end_time - start_time) * 1000, 4)
            if time_ms > 20:
                logging.error(f'message=Processing time is too long, sensor={message.sensor}, trace_id={trace_id}, processing_time={time_ms}ms')
                parent_span.add_event("Processing time is too long")
            elif 15 < time_ms <= 20:
                parent_span.add_event("Processing time is high")
                logging.warning(f'message=Processing time is high, sensor={message.sensor}, trace_id={trace_id}, processing_time={time_ms}ms')
            else:
                logging.info(f'message=Total processing time, sensor={message.sensor}, processing_time={time_ms}ms')
            parent_span.set_attribute('sensor', message.sensor)
            parent_span.set_attribute('processing_time', time_ms)


if __name__ == '__main__':
    app.main()
