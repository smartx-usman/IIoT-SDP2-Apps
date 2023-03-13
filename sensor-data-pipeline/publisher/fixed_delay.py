import logging
import sys

from delay_type import DelayType
from value_type_abnormal import ValueTypeAbnormal
from value_type_mixed import ValueTypeMixed
from value_type_normal import ValueTypeNormal

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


class DelayTypeFixed(DelayType):
    def __init__(self, value_type):
        self.value_type = value_type

    def add_delay(self, client, client_id, arguments):
        """Process Fixed delay"""
        if self.value_type == 'normal':
            value_type = ValueTypeNormal(client=client, client_id=client_id, delay=[float(arguments.delay[0])],
                                         mqtt_topic=arguments.mqtt_topic[0],
                                         normal_input=arguments.normal_input_file[0])
            value_type.process_data()
        elif self.value_type == 'abnormal':
            value_type = ValueTypeAbnormal(client=client, client_id=client_id, delay=[float(arguments.delay[0])],
                                           mqtt_topic=arguments.mqtt_topic[0],
                                           normal_input=arguments.normal_input_file[0],
                                           abnormal_input=arguments.abnormal_input_file[0])
            value_type.process_data()
        elif self.value_type == 'mixed':
            value_type = ValueTypeMixed(client=client, client_id=client_id, delay=[float(arguments.delay[0])],
                                        mqtt_topic=arguments.mqtt_topic[0],
                                        invalid_value_occurrence=arguments.invalid_value_occurrence[0],
                                        normal_input=arguments.normal_input_file[0],
                                        abnormal_input=arguments.abnormal_input_file[0])
            value_type.process_data()
        else:
            logging.error(f'Invalid data value_type is provided: {arguments.value_type[0]}')
            sys.exit(1)
