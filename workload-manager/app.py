import json
import logging
import os
import subprocess
import threading
import time

import kubernetes
import yaml
from flask import Flask, render_template, request, jsonify
from kubernetes.client.rest import ApiException
from kubernetes import utils

app = Flask(__name__)

WORKLOADS_NAMESPACE = os.environ['WORKLOADS_NAMESPACE']
UPLOAD_FOLDER = os.environ['UPLOAD_FOLDER']
KUBECONFIG_PATH = '/home/.kube/config'
WORKLOAD_TYPES_FILE = '/mnt/data/workload_types.json'

# Suppress Flask's default logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Default workload types
default_workload_types = [
    {"workload_key": "coap-server", "workload_display_name": "CoAP Server App", "workload_enabled": True},
    {"workload_key": "cpu-burner", "workload_display_name": "CPU Burner", "workload_enabled": True},
    {"workload_key": "disk-burner", "workload_display_name": "Disk Burner", "workload_enabled": True},
    {"workload_key": "file-server", "workload_display_name": "File Server App", "workload_enabled": True},
    {"workload_key": "iot-sensor-pipeline", "workload_display_name": "IoT Sensor Data Processing App",
     "workload_enabled": True},
    {"workload_key": "memory-burner", "workload_display_name": "Memory Burner", "workload_enabled": True},
    {"workload_key": "network-burner", "workload_display_name": "Network Burner", "workload_enabled": True},
    {"workload_key": "web-server", "workload_display_name": "Web Server App", "workload_enabled": True},
]


def initialize_workload_types():
    if not os.path.exists(WORKLOAD_TYPES_FILE):
        with open(WORKLOAD_TYPES_FILE, 'w') as file:
            json.dump(default_workload_types, file)


def get_cluster_nodes():
    load_kube_config()
    api_instance = kubernetes.client.CoreV1Api()
    nodes = api_instance.list_node()
    worker_nodes = [node.metadata.name for node in nodes.items if
                    "node-role.kubernetes.io/control-plane" not in node.metadata.labels]
    return worker_nodes


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/nodes', methods=['GET'])
def get_nodes():
    load_kube_config()
    v1 = kubernetes.client.CoreV1Api()
    ret = v1.list_node()
    nodes = []
    for i in ret.items:
        for condition in i.status.conditions:
            if condition.type == 'Ready' and condition.status == 'True' and "node-role.kubernetes.io/control-plane" not in i.metadata.labels:
                for address in i.status.addresses:
                    if address.type == 'Hostname':
                        nodes.append(address.address)
    return jsonify({"nodes": nodes})


@app.route('/workload_types', methods=['GET'])
def get_workload_types():
    if os.path.exists(WORKLOAD_TYPES_FILE):
        with open(WORKLOAD_TYPES_FILE, 'r') as file:
            workload_types = json.load(file)
    else:
        workload_types = default_workload_types

    return jsonify({"types": workload_types})


@app.route('/add_workload_type', methods=['POST'])
def add_workload_type():
    try:
        # new_workload_type = request.json

        # workload_yaml = request.files.get('workload_yaml')
        workload_key = request.form.get('workload_key')
        workload_display_name = request.form.get('workload_display_name')
        workload_enabled = request.form.get('workload_enabled')
        # workload_yaml = request.files.get('workload_yaml')
        workload_yaml = request.files.getlist('files')

        if not workload_key or not workload_display_name or not workload_yaml:
            return jsonify(status='error', message='Missing required fields'), 400

        if not os.path.exists(f'{UPLOAD_FOLDER}/{workload_key}'):
            os.makedirs(f'{UPLOAD_FOLDER}/{workload_key}')

        # workload_yaml.save(os.path.join(f'{UPLOAD_FOLDER}/{workload_key}', workload_yaml.filename))
        for file in workload_yaml:
            if file and file.filename.endswith('.yaml'):
                file_path = os.path.join(f'{UPLOAD_FOLDER}/{workload_key}', file.filename)
                file.save(file_path)

        workload_types = get_workload_types_from_file()

        # Ensure that data is a list
        if not isinstance(workload_types, list):
            workload_types = [workload_types]

        new_workload_type = {"workload_key": workload_key,
                             "workload_display_name": workload_display_name,
                             "workload_enabled": workload_enabled}

        workload_types.append(new_workload_type)
        save_workload_types_to_file(workload_types)
        return jsonify({"status": "success", "message": "Workload type added successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


def get_workload_types_from_file():
    if os.path.exists(WORKLOAD_TYPES_FILE):
        with open(WORKLOAD_TYPES_FILE, 'r') as file:
            return json.load(file)
    return default_workload_types


def save_workload_types_to_file(workload_types):
    try:
        with open(WORKLOAD_TYPES_FILE, 'w') as file:
            json.dump(workload_types, file)
        logging.info('Added new workload type successfully.')
    except FileNotFoundError as e:
        logging.error(f"Error saving new workload type to file: {e}")
    except json.JSONDecodeError:
        # If the file is empty or not in proper JSON format, create a new list
        with open(WORKLOAD_TYPES_FILE, 'w') as file:
            json.dump([workload_types], file, indent=4)
        logging.warning("File was empty or invalid JSON. Created a new file with the workload type.")
    except Exception as e:
        logging.error(f"An error occurred in save_workload_types_to_file: {e}")


def load_kube_config():
    try:
        kubernetes.config.load_kube_config(config_file=KUBECONFIG_PATH)  # This looks for ~/.kube/config by default
    except kubernetes.config.ConfigException as e:
        logging.error(f"Could not load kube config: {e}")
        raise


@app.route('/submit', methods=['POST'])
def submit():
    try:
        workloads = []
        chained = False
        workload_types = request.form.getlist('workload_type[]')
        durations = request.form.getlist('duration[]')
        durations = [int(duration) for duration in durations]
        replicas = request.form.getlist('replicas[]')
        node_names = request.form.getlist('node_name[]')

        for i in range(len(workload_types)):
            workloads.append({
                'type': workload_types[i],
                'duration': int(durations[i]),
                'replicas': int(replicas[i]),
                'node_name': node_names[i]
            })

        threading.Thread(target=handle_workloads, args=(workloads, chained)).start()

        return jsonify({"status": "success", "message": "Workload submitted successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


def handle_workloads(workloads, chained=False):
    for workload in workloads:
        threading.Thread(target=create_and_delete_resources, args=(workload, chained)).start()


def create_and_delete_resources(workload, chained):
    load_kube_config()
    api_instance_apps = kubernetes.client.AppsV1Api()
    api_instance_batch = kubernetes.client.BatchV1Api()
    api_instance_core = kubernetes.client.CoreV1Api()

    create_namespace(api_instance_core, WORKLOADS_NAMESPACE)

    deployment_dir = get_deployment_files_path(workload['type'])
    resources = []

    if workload['type'] == 'iot-sensor-pipeline':
        helm_mqtt_repo = ['helm', 'repo', 'add', 't3n', 'https://storage.googleapis.com/t3n-helm-charts']
        helm_bitnami_repo = ['helm', 'repo', 'add', 'bitnami', 'https://charts.bitnami.com/bitnami']
        subprocess.run(helm_mqtt_repo, check=True)
        subprocess.run(helm_bitnami_repo, check=True)

        helm_mqtt_command = ['helm', '-n', WORKLOADS_NAMESPACE, 'upgrade', '--install', 'mqtt',
                             '--kubeconfig', f'{KUBECONFIG_PATH}',
                             '-f', f'{deployment_dir}/brokers/mqtt-values.yaml', 't3n/mosquitto']
        helm_kafka_command = ['helm', '-n', WORKLOADS_NAMESPACE, 'upgrade', '--install', 'kafka',
                              '--kubeconfig', f'{KUBECONFIG_PATH}',
                              '-f', f'{deployment_dir}/brokers/kafka-values.yaml', 'bitnami/kafka']
        helm_mysql_command = ['helm', '-n', WORKLOADS_NAMESPACE, 'upgrade', '--install', 'mysql',
                              '--kubeconfig', f'{KUBECONFIG_PATH}',
                              '-f', f'{deployment_dir}/datastores/mysql-values.yaml', 'bitnami/mysql']

        subprocess.run(helm_mqtt_command, check=True)
        subprocess.run(helm_kafka_command, check=True)
        subprocess.run(helm_mysql_command, check=True)
        time.sleep(30)

    for filename in os.listdir(deployment_dir):
        if filename.endswith('.yaml'):
            with open(os.path.join(deployment_dir, filename), 'r') as file:
                documents = yaml.safe_load_all(file)
                for doc in documents:
                    resources.append(doc)

                    try:
                        """ Set nodeSelector for Deployment, StatefulSet, and Job resources """
                        if doc['kind'] in ['Deployment', 'StatefulSet', 'Job'] and workload['node_name'] != 'any':
                            doc['spec']['template']['spec']['nodeSelector'] = {
                                'kubernetes.io/hostname': workload['node_name']}

                        deploy_object(namespace=WORKLOADS_NAMESPACE, doc=doc, api_instance_apps=api_instance_apps,
                                      api_instance_core=api_instance_core, api_instance_batch=api_instance_batch,
                                      replicas=workload['replicas'])

                    except ApiException as e:
                        logging.warning(f"Exception when creating {doc['kind']} {filename}: {e}")

    logging.info(f"Workload '{workload}' created successfully.")
    logging.info(f"Workload will be running for '{workload['duration']}'s.")
    time.sleep(workload['duration'])

    for doc in resources:
        try:
            if doc['kind'] == 'Deployment':
                api_instance_apps.delete_namespaced_deployment(
                    name=doc['metadata']['name'],
                    namespace=WORKLOADS_NAMESPACE,
                    body=kubernetes.client.V1DeleteOptions(propagation_policy='Foreground')
                )
            elif doc['kind'] == 'StatefulSet':
                api_instance_apps.delete_namespaced_stateful_set(
                    name=doc['metadata']['name'],
                    namespace=WORKLOADS_NAMESPACE,
                    body=kubernetes.client.V1DeleteOptions(propagation_policy='Foreground')
                )
            elif doc['kind'] == 'Job':
                api_instance_batch.delete_namespaced_job(
                    name=doc['metadata']['name'],
                    namespace=WORKLOADS_NAMESPACE,
                    body=kubernetes.client.V1DeleteOptions(propagation_policy='Foreground')
                )
            elif doc['kind'] == 'Service':
                api_instance_core.delete_namespaced_service(
                    name=doc['metadata']['name'],
                    namespace=WORKLOADS_NAMESPACE
                )
            elif doc['kind'] == 'Namespace':
                api_instance_core.delete_namespace(
                    name=doc['metadata']['name'],
                    body=kubernetes.client.V1DeleteOptions(propagation_policy='Foreground')
                )

        except ApiException as e:
            print(f"Exception when deleting {doc['kind']} {doc['metadata']['name']}: {e}")

    if workload['type'] == 'iot-sensor-pipeline':
        helm_mqtt_delete = ['helm', 'delete', 'mqtt', '--kubeconfig', f'{KUBECONFIG_PATH}', '-n', 'workloads']
        helm_kafka_delete = ['helm', 'delete', 'kafka', '--kubeconfig', f'{KUBECONFIG_PATH}', '-n', 'workloads']
        helm_mysql_delete = ['helm', 'delete', 'mysql', '--kubeconfig', f'{KUBECONFIG_PATH}', '-n', 'workloads']
        subprocess.run(helm_mqtt_delete, check=True)
        subprocess.run(helm_kafka_delete, check=True)
        subprocess.run(helm_mysql_delete, check=True)

    logging.info(f"Workload '{workload}' deleted successfully.")


def create_namespace(api_instance_core, namespace_name):
    ns = kubernetes.client.V1Namespace(metadata=kubernetes.client.V1ObjectMeta(name=namespace_name))
    try:
        api_instance_core.create_namespace(ns)
        logging.info(f"Namespace '{namespace_name}' created.")
    except ApiException as e:
        if e.status == 409:
            logging.info(f"Namespace '{namespace_name}' already exists. So skipping this step.")
        else:
            logging.error(f"Error creating namespace '{namespace_name}': {e}")


def get_deployment_files_path(workload_type):
    return f'workloads/{workload_type.lower()}'


@app.route('/monitoring', methods=['POST'])
def deploy_monitoring_system():
    try:
        selected_option = request.form.get('options')
        namespace = 'monitoring'
        deployment_dir = 'monitoring'

        load_kube_config()
        api_instance_core = kubernetes.client.CoreV1Api()
        api_instance_apps = kubernetes.client.AppsV1Api()
        api_instance_rbac = kubernetes.client.RbacAuthorizationV1Api()

        if selected_option == 'deploy':
            try:
                api_instance_core.read_namespace(name=namespace)
                logging.info(f"Namespace '{namespace}' already exists. So skipping this step.")
            except ApiException as e:
                if e.status == 404:
                    logging.info(f"Namespace '{namespace}' does not exist. Creating it...")
                    create_namespace(api_instance_core, namespace)
                    logging.info(f"Namespace '{namespace}' created.")
                else:
                    logging.error(f"An error occurred: {e}")

            # Deploy/Delete Prometheus and Grafana
            repo = ['helm', 'repo', 'add', 'prometheus-community', 'https://prometheus-community.github.io/helm-charts']
            subprocess.run(repo, check=True)

            repo = ['helm', 'repo', 'add', 'grafana', 'https://grafana.github.io/helm-charts']
            subprocess.run(repo, check=True)

            command = ['helm', '-n', f'{namespace}', 'upgrade', '--install', 'prometheus', '--kubeconfig', f'{KUBECONFIG_PATH}',
                       '-f', f'{deployment_dir}/prometheus.yaml', 'prometheus-community/prometheus']
            subprocess.run(command, check=True)

            command = ['helm', '-n', f'{namespace}', 'upgrade', '--install', 'grafana',
                       '--kubeconfig', f'{KUBECONFIG_PATH}', '-f', f'{deployment_dir}/grafana.yaml', 'grafana/grafana']
            subprocess.run(command, check=True)

            time.sleep(15)

            files = ['telegraf-serviceaccount.yaml', 'telegraf.yaml']

            for filename in files:
                logging.info(f"Deploying {filename}")
                with open(os.path.join(deployment_dir, filename), 'r') as file:
                    documents = yaml.safe_load_all(file)
                    for doc in documents:
                        deploy_object(namespace=namespace, doc=doc, api_instance_apps=api_instance_apps,
                                      api_instance_core=api_instance_core, api_instance_rbac=api_instance_rbac)

        else:
            try:
                api_instance_rbac.delete_cluster_role_binding(name='k8s-telegraf-viewer-mon')
                api_instance_rbac.delete_cluster_role(name='k8s-stats-viewer-mon')
                api_instance_rbac.delete_cluster_role(name='k8s-telegraf-mon')

                logging.info(f"ClusterRole and ClusterRoleBinding deleted.")
            except ApiException as e:
                if e.status == 404:
                    logging.info(f"ClusterRole or ClusterRoleBinding does not exist.")
                else:
                    logging.error(f"An error occurred while deleting ClusterRole or ClusterRoleBinding': {e}")

            try:
                api_instance_core.read_namespace(name=namespace)

                api_response = api_instance_core.delete_namespace(namespace)
                logging.info(f"Namespace deleted. status='{api_response.status}'")

            except ApiException as e:
                if e.status == 404:
                    logging.info(f"Namespace '{namespace}' does not exist.")
                else:
                    logging.error(f"An error occurred: {e}")

        time.sleep(10)

        return jsonify({"status": "success", "message": f"Monitoring system {selected_option} request submitted successfully."})
    except Exception as e:
        logging.error(str(e))
        return jsonify({"status": "error", "message": str(e)})


def deploy_object(namespace, doc, api_instance_apps, api_instance_core, api_instance_rbac=None, api_instance_batch=None,
                  replicas=1):
    if doc['kind'] == 'ClusterRole':
        utils.create_from_dict(api_instance_rbac.api_client, doc)
        logging.info(f"ClusterRole '{doc['metadata']['name']}' created.")

    elif doc['kind'] == 'ClusterRoleBinding':
        utils.create_from_dict(api_instance_rbac.api_client, doc)
        logging.info(f"ClusterRoleBinding '{doc['metadata']['name']}' created.")

    elif doc['kind'] == 'ConfigMap':
        api_instance_core.create_namespaced_config_map(namespace=namespace, body=doc)
        logging.info(f"ConfigMap '{doc['metadata']['name']}' created.")

    elif doc['kind'] == 'Secret':
        api_instance_core.create_namespaced_secret(namespace=namespace, body=doc)
        logging.info(f"Secret '{doc['metadata']['name']}' created.")

    elif doc['kind'] == 'DaemonSet':
        api_instance_apps.create_namespaced_daemon_set(namespace=namespace, body=doc)
        logging.info(f"Daemonset '{doc['metadata']['name']}' created.")

    elif doc['kind'] == 'Deployment':
        doc['spec']['replicas'] = int(replicas)
        api_instance_apps.create_namespaced_deployment(namespace=namespace, body=doc)
        logging.info(f"Deployment '{doc['metadata']['name']}' created.")

    elif doc['kind'] == 'Job':
        api_instance_batch.create_namespaced_job(namespace=WORKLOADS_NAMESPACE, body=doc)
        logging.info(f"Job '{doc['metadata']['name']}' created.")

    elif doc['kind'] == 'ServiceAccount':
        api_instance_core.create_namespaced_service_account(namespace=namespace, body=doc)
        logging.info(f"ServiceAccount '{doc['metadata']['name']}' created.")

    elif doc['kind'] == 'Service':
        api_instance_core.create_namespaced_service(namespace=namespace, body=doc)
        logging.info(f"Service '{doc['metadata']['name']}' created.")

    elif doc['kind'] == 'StatefulSet':
        doc['spec']['replicas'] = int(replicas)
        api_instance_apps.create_namespaced_stateful_set(namespace=namespace, body=doc)

    elif doc['kind'] == 'Namespace':
        api_instance_core.create_namespace(body=doc)

    else:
        logging.warning(f"Unknown resource type: {doc['kind']}")


if __name__ == '__main__':
    initialize_workload_types()
    app.run(host='0.0.0.0', port=9000, debug=False)
