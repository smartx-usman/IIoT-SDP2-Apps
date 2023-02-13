import logging
import time

from value_type import ValueType

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


class ValueTypeMixed(ValueType):
    def __init__(self, client, client_id, delay, mqtt_topic, invalid_value_occurrence, normal_input, abnormal_input):
        self.client = client
        self.client_id = client_id
        self.delay = delay
        self.mqtt_topic = mqtt_topic
        self.invalid_value_occurrence = invalid_value_occurrence
        self.normal_input_file = normal_input
        self.abnormal_input_file = abnormal_input

    def process_data(self):
        # Check delay type
        if len(self.delay) == 1:
            # msg_count = 1
            while True:
                # start_time = time.perf_counter()
                with open(f'/data/{self.normal_input_file}') as fp_normal:
                    values = fp_normal.readlines()
                    with open(f'/data/{self.abnormal_input_file}') as fp_abnormal:
                        abnormal_values = fp_abnormal.readlines()

                    current_value_index = 0
                    count = 1

                    for value in values:
                        if count == int(self.invalid_value_occurrence):
                            # for abnormal_value in abnormal_values:
                            value = abnormal_values[current_value_index]
                            # value = arguments.invalid_value[0]
                            current_value_index = current_value_index + 1
                            count = 0

                        time_ms = round(time.time() * 1000)

                        value = value.strip().split(',')

                        telemetry = "{"
                        telemetry += "\"measurement_ts\":" + str(time_ms) + ",";
                        telemetry += "\"temperature\":" + str(value[0]) + ",";
                        telemetry += "\"humidity\":" + str(value[1]) + ",";
                        telemetry += "\"sensor\":" + str(self.client_id);
                        telemetry += "}"

                        # msg = f"measurement_ts: {time_ms} sensor: {self.client_id} value: {str(value).strip()}"
                        result = self.client.publish(self.mqtt_topic, telemetry, 0, False)
                        status = result[0]

                        logging.info(
                            f"Message: Successful to send message, Sensor: {str(self.client_id)}, Status: {status}") if status == 0 else logging.error(
                            f"Message: Failed to send message, Sensor: {str(self.client_id)}, Status: {status}")

                        count += 1
                        # msg_count += 1
                        time.sleep(self.delay[0])
                # end_time = time.perf_counter()
                # logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete one iteration.')
        else:
            while True:
                delay_index = 0
                with open(f'/data/{self.normal_input_file}') as fp_normal:
                    values = fp_normal.readlines()
                    with open(f'/data/{self.abnormal_input_file}') as fp_abnormal:
                        abnormal_values = fp_abnormal.readlines()

                    current_value_index = 0
                    count = 1

                    for value in values:
                        if count == int(self.invalid_value_occurrence):
                            # for abnormal_value in abnormal_values:
                            value = abnormal_values[current_value_index]
                            # value = arguments.invalid_value[0]
                            current_value_index = current_value_index + 1
                            count = 0

                        time_ms = round(time.time() * 1000)
                        # msg = f"measurement_ts: {time_ms} sensor: {self.client_id} value: {str(value).strip()}"

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

                        time.sleep(self.delay[delay_index])
                        count += 1
                        delay_index += 1
                        if delay_index == len(self.delay):
                            delay_index = 0
