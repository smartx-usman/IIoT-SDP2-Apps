import os

from config import Config

def get_deployment_files_path(workload_name, username):
    if workload_name in ("coap-server", "cpu-burner", "disk-burner", "file-server", "memory-burner", "network-burner",
                       "web-server", "data-generator", "data-publisher", "data-subscriber", "data-analyzer",
                       "data-actuator", "data-ui", "mqtt-broker", "kafka-broker", "mysql-server") or username == 'admin':
        return os.path.join(Config.UPLOAD_FOLDER, str(workload_name))
    return os.path.join(Config.UPLOAD_FOLDER, username, str(workload_name))