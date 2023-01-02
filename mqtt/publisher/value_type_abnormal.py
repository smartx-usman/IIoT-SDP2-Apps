import logging
import time

#from tb_device_mqtt import TBPublishInfo
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
            # msg_count = 1
            while True:
                # start_time = time.perf_counter()

                with open(f'/data/{self.abnormal_input_file}') as fp:
                    values = fp.readlines()
                    for value in values:
                        time_ms = round(time.time() * 1000)

                        # telemetry = {"measurement_ts": time_ms,
                        #             "temperature": str(value).strip(),
                        #             "sensor": self.client_id}
                        value = value.strip().split(',')

                        telemetry = "{"
                        telemetry += "\"measurement_ts\":" + str(time_ms) + ",";
                        telemetry += "\"temperature\":" + str(value[0]) + ",";
                        telemetry += "\"humidity\":" + str(value[1]) + ",";
                        telemetry += "\"sensor\":" + str(self.client_id);
                        telemetry += "}"

                        result = self.client.publish(self.mqtt_topic, telemetry, 0, False)
                        status = result[0]

                        #result = self.client.send_telemetry(telemetry)
                        #success = result.get() == TBPublishInfo.TB_ERR_SUCCESS

                        #logging.info(f"{telemetry}") if result.get() == 0 else logging.error(
                        logging.info(f"Message - {telemetry} Status - {status}") if status == 0 else logging.error(
                            f"Failed to send message to topic {self.mqtt_topic}")

                        # msg_count += 1
                        time.sleep(self.delay[0])

                # end_time = time.perf_counter()
                # logging.info(f'It took {end_time - start_time: 0.4f} second(s) to complete one iteration.')
        else:
            while True:
                delay_index = 0
                with open(f'/data/{self.abnormal_input_file}') as fp:
                    values = fp.readlines()
                    for value in values:
                        time_ms = round(time.time() * 1000)

                        # telemetry = {"measurement_ts": time_ms,
                        #             "temperature": str(value).strip(),
                        #             "sensor": self.client_id}

                        value = value.strip().split(',')

                        telemetry = "{"
                        telemetry += "\"measurement_ts\":" + str(time_ms) + ",";
                        telemetry += "\"temperature\":" + str(value[0]) + ",";
                        telemetry += "\"humidity\":" + str(value[1]) + ",";
                        telemetry += "\"sensor\":" + str(self.client_id);
                        telemetry += "}"

                        result = self.client.publish(self.mqtt_topic, telemetry, 0, False)
                        status = result[0]

                        #result = self.client.send_telemetry(telemetry)

                        #logging.info(f"{telemetry}") if result.get() == 0 else logging.error(
                        logging.info(f"Message - {telemetry} Status - {status}") if status == 0 else logging.error(
                            f"Failed to send message to topic {self.mqtt_topic}")

                        time.sleep(self.delay[delay_index])

                        delay_index = delay_index + 1
                        if delay_index == len(self.delay):
                            delay_index = 0

        #mosquitto_pub -t "v1/devices/me/telemetry" -h 130.243.26.28 -p 30320 -u 0iKj6GLHWJDLHwJ9RPsj -m '{"serialNumber": "SN-001", "sensorType": "Thermometer", "sensorModel": "T1000", "temp": 42, "hum": 58}'
        #mosquitto_sub -t "v1/devices/me/telemetry" -h thingsboard-mqtt.thingsboard.svc.cluster.local -p 1883 -u 0iKj6GLHWJDLHwJ9RPsj

