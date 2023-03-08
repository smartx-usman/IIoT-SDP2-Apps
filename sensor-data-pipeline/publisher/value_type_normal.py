import logging
import time

from value_type import ValueType

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


class ValueTypeNormal(ValueType):
    def __init__(self, client, client_id, delay, mqtt_topic, normal_input):
        self.client = client
        self.client_id = client_id
        self.delay = delay
        self.mqtt_topic = mqtt_topic
        self.normal_input_file = normal_input

    def process_data(self):
        # Check delay type
        if len(self.delay) == 1:
            while True:
                # start_time = time.perf_counter()
                with open(f'/data/{self.normal_input_file}') as fp:
                    values = fp.readlines()
                    for value in values:
                        time_ms = round(time.time() * 1000)
                        value = value.strip().split(',')

                        telemetry = "{"
                        telemetry += "\"measurement_ts\":" + str(time_ms) + ",";
                        telemetry += "\"temperature\":" + str(value[0]) + ",";
                        telemetry += "\"humidity\":" + str(value[1]) + ",";
                        telemetry += "\"sensor\":" + str(self.client_id);
                        telemetry += "}"

                        result = self.client.publish(self.mqtt_topic, telemetry, 0, False)
                        status = result[0]

                        logging.info(
                            f"Message: Successful to send message, Sensor: {str(self.client_id)}, Status: {status}") if status == 0 else logging.error(
                            f"Message: Failed to send message, Sensor: {str(self.client_id)}, Status: {status}")

                        time.sleep(self.delay[0])

                # end_time = time.perf_counter()
                # logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete one iteration.')
        else:
            while True:
                delay_index = 0
                with open(f'/data/{self.normal_input_file}') as fp:
                    values = fp.readlines()
                    for value in values:
                        time_ms = round(time.time() * 1000)

                        telemetry = "{"
                        telemetry += "\"measurement_ts\":" + str(time_ms) + ",";
                        telemetry += "\"temperature\":" + str(value[0]) + ",";
                        telemetry += "\"humidity\":" + str(value[1]) + ",";
                        telemetry += "\"sensor\":" + str(self.client_id);
                        telemetry += "}"

                        result = self.client.publish(self.mqtt_topic, telemetry, 0, False)
                        status = result[0]

                        logging.info(
                            f"Message: Successful to send message, Sensor: {str(self.client_id)}, Status: {status}") if status == 0 else logging.error(
                            f"Message: Failed to send message, Sensor: {str(self.client_id)}, Status: {status}")

                        time.sleep(self.delay[delay_index])

                        delay_index = delay_index + 1
                        if delay_index == len(self.delay):
                            delay_index = 0
