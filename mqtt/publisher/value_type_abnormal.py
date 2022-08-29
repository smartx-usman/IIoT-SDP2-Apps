import logging
import time

from value_type import ValueType

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


class ValueTypeAbnormal(ValueType):
    def __init__(self, client, client_id, delay, mqtt_topic, normal_input, abnormal_input):
        self.client = client
        self.client_id = client_id
        self.delay = delay
        self.mqtt_topic = mqtt_topic
        self.normal_input_file = normal_input
        self.abnormal_input_file = abnormal_input

    def process_data(self):
        # Check delay type
        if len(self.delay) == 1:
            msg_count = 1
            while True:
                start_time = time.perf_counter()

                with open(f'/data/{self.abnormal_input_file}') as fp:
                    values = fp.readlines()
                    for value in values:
                        time_ms = round(time.time() * 1000)
                        msg = f"measurement_ts: {time_ms} client_id: {self.client_id} msg_count: {msg_count} value: {str(value).strip()}"
                        result = self.client.publish(self.mqtt_topic, msg)
                        status = result[0]

                        if status == 0:
                            logging.info(f"Send `{msg}` to topic `{self.mqtt_topic}`")
                        else:
                            logging.error(f"Failed to send message to topic {self.mqtt_topic}")

                        msg_count += 1
                        time.sleep(self.delay[0])

                end_time = time.perf_counter()
                logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete one iteration.')
        else:
            msg_count = 1
            while True:
                start_time = time.perf_counter()
                delay_index = 0
                with open(f'/data/{self.abnormal_input_file}') as fp:
                    values = fp.readlines()
                    for value in values:
                        time_ms = round(time.time() * 1000)
                        msg = f"measurement_ts: {time_ms} client_id: {self.client_id} msg_count: {msg_count} value: {str(value).strip()}"
                        result = self.client.publish(self.mqtt_topic, msg)
                        status = result[0]

                        if status == 0:
                            logging.info(f"Send `{msg}` to topic `{self.mqtt_topic}`")
                        else:
                            logging.error(f"Failed to send message to topic {self.mqtt_topic}")

                        msg_count += 1
                        time.sleep(self.delay[delay_index])

                        delay_index = delay_index + 1
                        if delay_index == len(self.delay):
                            delay_index = 0

                end_time = time.perf_counter()
                logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete one iteration.')
