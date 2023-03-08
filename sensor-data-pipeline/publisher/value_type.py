import abc


class ValueType(abc.ABC):
    client = ''
    client_id = ''
    delay = {}
    mqtt_topic = ''
    invalid_value_occurrence = ''
    normal_input_file = ''
    abnormal_input_file = ''

    @abc.abstractmethod
    def process_data(self):
        pass
