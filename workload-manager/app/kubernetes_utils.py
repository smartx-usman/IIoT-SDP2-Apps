import logging
import os
import subprocess
import threading
import time
from datetime import datetime

import kubernetes
import yaml
from kubernetes import utils
from kubernetes.client.rest import ApiException
from config import Config
from app import create_app, db

from app.models import DeployedWorkload


def load_kube_config():
    try:
        kubernetes.config.load_kube_config(
            config_file=Config.KUBECONFIG_PATH)  # This looks for ~/.kube/config by default
    except kubernetes.config.ConfigException as e:
        logging.error(f"Could not load kube config: {e}")
        raise


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


def process_object(namespace, doc, option, api_instance_apps, api_instance_core, api_instance_rbac=None,
                   api_instance_batch=None,
                   replicas=1):
    if option == 'install':
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
            api_instance_batch.create_namespaced_job(namespace=Config.WORKLOADS_NAMESPACE, body=doc)
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
    else:
        if doc['kind'] == 'Deployment':
            api_instance_apps.delete_namespaced_deployment(
                name=doc['metadata']['name'], namespace=namespace,
                body=kubernetes.client.V1DeleteOptions(propagation_policy='Foreground')
            )
        elif doc['kind'] == 'StatefulSet':
            api_instance_apps.delete_namespaced_stateful_set(
                name=doc['metadata']['name'], namespace=namespace,
                body=kubernetes.client.V1DeleteOptions(propagation_policy='Foreground')
            )
        elif doc['kind'] == 'Job':
            api_instance_batch.delete_namespaced_job(
                name=doc['metadata']['name'], namespace=namespace,
                body=kubernetes.client.V1DeleteOptions(propagation_policy='Foreground')
            )
        elif doc['kind'] == 'Service':
            api_instance_core.delete_namespaced_service(
                name=doc['metadata']['name'], namespace=namespace
            )
        elif doc['kind'] == 'Namespace':
            api_instance_core.delete_namespace(
                name=doc['metadata']['name'], body=kubernetes.client.V1DeleteOptions(propagation_policy='Foreground')
            )
        else:
            logging.warning(f"Unknown resource type: {doc['kind']}")


def process_helm(command):
    subprocess.run(command, check=True, shell=True)


# def get_deployment_files_path(workload_type):
#    return f'workloads/{workload_type.lower()}'
def get_deployment_files_path(workload_id):
    return os.path.join(Config.UPLOAD_FOLDER, str(workload_id))


def handle_workloads(workloads, chained=False, username=None):
    for workload in workloads:
        threading.Thread(target=create_and_delete_resources, args=(workload, chained, username)).start()


def create_and_delete_resources(workload, chained, username):
    app = create_app()

    with app.app_context():  # Manually push the application context
        load_kube_config()
        api_instance_apps = kubernetes.client.AppsV1Api()
        api_instance_batch = kubernetes.client.BatchV1Api()
        api_instance_core = kubernetes.client.CoreV1Api()

        create_namespace(api_instance_core, Config.WORKLOADS_NAMESPACE)
        deployment_dir = get_deployment_files_path(workload['type'].lower())
        resources = []

        if workload['type'] == 'iot-sensor-pipeline':
            commands = ['helm repo add t3n https://storage.googleapis.com/t3n-helm-charts',
                        'helm repo add bitnami https://charts.bitnami.com/bitnami',
                        f'helm -n {Config.WORKLOADS_NAMESPACE} upgrade --install mqtt --kubeconfig {Config.KUBECONFIG_PATH} -f {deployment_dir}/brokers/mqtt-values.yaml t3n/mosquitto',
                        f'helm -n {Config.WORKLOADS_NAMESPACE} upgrade --install kafka --kubeconfig {Config.KUBECONFIG_PATH} -f {deployment_dir}/brokers/kafka-values.yaml bitnami/kafka',
                        f'helm -n {Config.WORKLOADS_NAMESPACE} upgrade --install mysql --kubeconfig {Config.KUBECONFIG_PATH} -f {deployment_dir}/datastores/mysql-values.yaml bitnami/mysql']

            for command in commands:
                process_helm(command)

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

                            process_object(namespace=Config.WORKLOADS_NAMESPACE, doc=doc, option='install',
                                           api_instance_apps=api_instance_apps, api_instance_core=api_instance_core,
                                           api_instance_batch=api_instance_batch, replicas=workload['replicas'])

                        except ApiException as e:
                            logging.warning(f"Exception when creating {doc['kind']} {filename}: {e}")

        # user_id = session['user_id']
        # workload_name = request.form.get('workload_name')
        # yaml_content = request.form.get('yaml_content')

        # Log the deployment action
        new_workload = DeployedWorkload(username=username,
                                        # workload_type_id=workload['id'],
                                        workload_name=workload['type'],
                                        duration=workload['duration'],
                                        replicas=workload['replicas'],
                                        node_name=workload['node_name'],
                                        status='success',
                                        created_at=datetime.utcnow())
        db.session.add(new_workload)
        db.session.commit()

        logging.info(f"Workload '{workload}' created successfully.")
        logging.info(f"Workload will be running for '{workload['duration']}'s.")
        time.sleep(workload['duration'])

        for doc in resources:
            try:
                process_object(namespace=Config.WORKLOADS_NAMESPACE, doc=doc, option='delete',
                               api_instance_apps=api_instance_apps,
                               api_instance_core=api_instance_core, api_instance_batch=api_instance_batch)

            except ApiException as e:
                print(f"Exception when deleting {doc['kind']} {doc['metadata']['name']}: {e}")

        if workload['type'] == 'iot-sensor-pipeline':
            commands = [f'helm delete mqtt --kubeconfig {Config.KUBECONFIG_PATH} -n {Config.WORKLOADS_NAMESPACE}',
                        f'helm delete kafka --kubeconfig {Config.KUBECONFIG_PATH} -n {Config.WORKLOADS_NAMESPACE}',
                        f'helm delete mysql --kubeconfig {Config.KUBECONFIG_PATH} -n {Config.WORKLOADS_NAMESPACE}']
            for command in commands:
                process_helm(command)

        logging.info(f"Workload '{workload}' deleted successfully.")


def get_cluster_nodes():
    load_kube_config()
    api_instance = kubernetes.client.CoreV1Api()
    nodes = api_instance.list_node()
    worker_nodes = [node.metadata.name for node in nodes.items if
                    "node-role.kubernetes.io/control-plane" not in node.metadata.labels]
    return worker_nodes


def process_helm_deployment(command):
    """Secure Helm deployment handler with namespace support"""
    full_cmd = command + [
        '--namespace', Config.WORKLOADS_NAMESPACE,
        '--kubeconfig', Config.KUBECONFIG_PATH
    ]

    try:
        result = subprocess.run(
            full_cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Helm deployment failed: {e.stderr}")
        return False, e.stderr