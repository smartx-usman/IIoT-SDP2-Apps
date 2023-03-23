"""
For generating synthetic data.
Version: 0.1.0
"""
import os


class ActionGenerator:
    def __init__(self, tracer, mqtt_client):
        self.tracer = tracer
        self.mqtt_client = mqtt_client
        self.actuator_id = 'actuator-0'
        self.actuator_actions = ['power-on', 'pause', 'shutdown']
        self.min_threshold_value = int(os.environ['MIN_THRESHOLD_VALUE'])
        self.max_threshold_value = int(os.environ['MAX_THRESHOLD_VALUE'])

    def parse_message_for_actuator(self, sensor, ts, action):
        """Parse message for MQTT"""
        with self.tracer.start_as_current_span("parser") as child_level2_span1:
            message = f"reading_ts:{ts} actuator_id:{self.actuator_id} sensor:{sensor} action:{action}"
            self.mqtt_client.publish_message(message=message)

    def get_actuator_action(self, sensor, value, ts):
        """Find action for the actuator"""
        with self.tracer.start_as_current_span("ruler") as child_level1_span1:
            if value < self.min_threshold_value:
                self.parse_message_for_actuator(sensor, ts, self.actuator_actions[0])
            elif value > self.max_threshold_value:
                self.parse_message_for_actuator(sensor, ts, self.actuator_actions[2])
            else:
                pass
