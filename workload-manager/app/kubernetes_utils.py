import logging
import os
import subprocess
import threading
import time
from datetime import datetime

import kubernetes
import yaml
from flask import jsonify
from kubernetes import client, config, dynamic, utils
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


def ensure_user_namespace(username, namespace, quota_pods, quota_cpu, quota_memory):
    load_kube_config()
    api = kubernetes.client.CoreV1Api()
    try:
        api.read_namespace(name=namespace)
        validate_resource_quota(namespace, quota_pods, quota_cpu, quota_memory)
        return True
    except ApiException as e:
        if e.status == 404:
            logging.info(f"Namespace '{namespace}' does not exist. Creating...")
            namespace_manifest = {
                'apiVersion': 'v1',
                'kind': 'Namespace',
                'metadata': {
                    'name': namespace,
                    'labels': {
                        'owner': username,
                        'created-by': 'workload-manager'
                    }
                }
            }
            try:
                api.create_namespace(body=namespace_manifest)
                time.sleep(5)

                validate_resource_quota(namespace, quota_pods, quota_cpu, quota_memory)
            except ApiException as e:
                logging.error(f"Error creating namespace {namespace}: {e}")
        else:
            logging.error(f"Error reading namespace {namespace}: {e}")


def validate_resource_quota(namespace, quota_pods, quota_cpu, quota_memory):
    api = kubernetes.client.CoreV1Api()
    try:
        quota = api.read_namespaced_resource_quota(
            name=f"{namespace}-quota",
            namespace=namespace
        )
    except ApiException as e:
        if e.status == 404:
            quota = {
                "apiVersion": "v1",
                "kind": "ResourceQuota",
                "metadata": {"name": f"{namespace}-quota"},
                "spec": {
                    "hard": {
                        "pods": f"{quota_pods}",
                        "requests.cpu": f"{quota_cpu}",
                        "requests.memory": f"{quota_memory}"
                    }
                }
            }
            api = kubernetes.client.CoreV1Api()
            api.create_namespaced_resource_quota(namespace, body=quota)
            logging.info(f"Namespace and Default quota created for namespace {namespace}")
        else:
            logging.error(f"Error reading resource quota for namespace {namespace}: {e}")
            raise


def create_kubernetes_objects(namespace, doc, api_instance_apps, api_instance_core, api_instance_rbac=None,
                              api_instance_batch=None, replicas=1):
    if doc['kind'] == 'ClusterRole':
        utils.create_from_dict(api_instance_rbac.api_client, doc)
    elif doc['kind'] == 'ClusterRoleBinding':
        utils.create_from_dict(api_instance_rbac.api_client, doc)
    elif doc['kind'] == 'ConfigMap':
        api_instance_core.create_namespaced_config_map(namespace=namespace, body=doc)
    elif doc['kind'] == 'Secret':
        api_instance_core.create_namespaced_secret(namespace=namespace, body=doc)
    elif doc['kind'] == 'DaemonSet':
        api_instance_apps.create_namespaced_daemon_set(namespace=namespace, body=doc)
    elif doc['kind'] == 'Pod':
        api_instance_core.create_namespaced_pod(namespace=namespace, body=doc)
    elif doc['kind'] == 'Deployment':
        doc['spec']['replicas'] = int(replicas)
        api_instance_apps.create_namespaced_deployment(namespace=namespace, body=doc)
    elif doc['kind'] == 'Job':
        api_instance_batch.create_namespaced_job(namespace=namespace, body=doc)
    elif doc['kind'] == 'ServiceAccount':
        api_instance_core.create_namespaced_service_account(namespace=namespace, body=doc)
    elif doc['kind'] == 'Service':
        api_instance_core.create_namespaced_service(namespace=namespace, body=doc)
    elif doc['kind'] == 'StatefulSet':
        doc['spec']['replicas'] = int(replicas)
        api_instance_apps.create_namespaced_stateful_set(namespace=namespace, body=doc)
    elif doc['kind'] == 'Namespace':
        api_instance_core.create_namespace(body=doc)
    else:
        logging.warning(f"Unknown resource type: {doc['kind']}")
    logging.info(f"{doc['kind']} '{doc['metadata']['name']}' created.")


def delete_kubernetes_objects(namespace, doc, api_instance_apps, api_instance_core, api_instance_batch=None):
    if doc['kind'] == 'Deployment':
        api_instance_apps.delete_namespaced_deployment(
            name=doc['metadata']['name'], namespace=namespace,
            body=kubernetes.client.V1DeleteOptions(propagation_policy='Foreground')
        )
    elif doc['kind'] == 'Pod':
        api_instance_core.delete_namespaced_pod(
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


def get_deployment_files_path(workload_id):
    return os.path.join(Config.UPLOAD_FOLDER, str(workload_id))


def handle_workloads(workloads, chained=False, username=None, namespace=None):
    for workload in workloads:
        threading.Thread(target=manage_kubernetes_resources, args=(workload, chained, username, namespace)).start()
        time.sleep(5)


def manage_kubernetes_resources(workload, chained, username, namespace):
    app = create_app()
    created_at = datetime.utcnow()

    with app.app_context():  # Manually push the application context
        load_kube_config()
        api_instance_apps = kubernetes.client.AppsV1Api()
        api_instance_batch = kubernetes.client.BatchV1Api()
        api_instance_core = kubernetes.client.CoreV1Api()

        # create_namespace(api_instance_core, Config.WORKLOADS_NAMESPACE)
        deployment_dir = get_deployment_files_path(workload['type'].lower())
        resources = []
        try:
            if workload['type'] == 'iot-sensor-pipeline':
                commands = ['helm repo add t3n https://storage.googleapis.com/t3n-helm-charts',
                            'helm repo add bitnami https://charts.bitnami.com/bitnami',
                            f'helm -n {namespace} upgrade --install mqtt --kubeconfig {Config.KUBECONFIG_PATH} -f {deployment_dir}/brokers/mqtt-values.yaml t3n/mosquitto',
                            f'helm -n {namespace} upgrade --install kafka --kubeconfig {Config.KUBECONFIG_PATH} -f {deployment_dir}/brokers/kafka-values.yaml bitnami/kafka',
                            f'helm -n {namespace} upgrade --install mysql --kubeconfig {Config.KUBECONFIG_PATH} -f {deployment_dir}/datastores/mysql-values.yaml bitnami/mysql']

                for command in commands:
                    process_helm(command)

                time.sleep(30)

            #logging.info(f"Deploying resources from '{deployment_dir}'...")
            replicas = workload.get('replicas', 1)  # Remove this line in future after migration to new schema
            for filename in os.listdir(deployment_dir):
                if filename.endswith('.yaml' or '.yml'):
                    with open(os.path.join(deployment_dir, filename), 'r') as file:
                        documents = yaml.safe_load_all(file)
                        for doc in documents:
                            resources.append(doc)

                            try:
                                if doc['kind'] in ['Pod'] and workload['node_name'] != 'any':
                                    doc['spec']['containers'][0]['nodeSelector'] = {
                                        'kubernetes.io/hostname': workload['node_name']}

                                if doc['kind'] in ['Deployment', 'StatefulSet', 'Job'] and workload['node_name'] != 'any':
                                    doc['spec']['template']['spec']['nodeSelector'] = {
                                        'kubernetes.io/hostname': workload['node_name']}

                                create_kubernetes_objects(namespace=namespace,
                                                          doc=doc,
                                                          api_instance_apps=api_instance_apps,
                                                          api_instance_core=api_instance_core,
                                                          api_instance_batch=api_instance_batch,
                                                          replicas=replicas)

                            except ApiException as e:
                                logging.warning(f"Exception when creating {doc['kind']} {filename}: {e}")

            # Log the deployment action
            new_workload = DeployedWorkload(username=username,
                                            workload_name=workload['type'],
                                            duration=workload['duration'],
                                            replicas=replicas,
                                            node_name=workload['node_name'],
                                            status='success',
                                            completed=False,
                                            created_at=created_at)
            db.session.add(new_workload)
            db.session.commit()

            logging.info(
                f"Workload '{workload['type']}' created in '{namespace}' and will run '{workload['duration']}'s.")
            #logging.info(f"Creation Time '{created_at}'.")

            time.sleep(workload['duration'])
            logging.info(f"Workload '{workload['type']}' completed. Deleting resources...")

            for resource in resources:
                logging.info(f"Deleting {resource['kind']} '{resource['metadata']['name']}'...")
                try:
                    delete_kubernetes_objects(namespace=namespace,
                                              doc=resource,
                                              api_instance_apps=api_instance_apps,
                                              api_instance_core=api_instance_core,
                                              api_instance_batch=api_instance_batch)

                except ApiException as e:
                    if not e.status == 404:
                        logging.warning(
                            f"Exception when deleting {resource['kind']} {resource['metadata']['name']}: {e}")

            if workload['type'] == 'iot-sensor-pipeline':
                commands = [f'helm delete mqtt --kubeconfig {Config.KUBECONFIG_PATH} -n {namespace}',
                            f'helm delete kafka --kubeconfig {Config.KUBECONFIG_PATH} -n {namespace}',
                            f'helm delete mysql --kubeconfig {Config.KUBECONFIG_PATH} -n {namespace}']
                for command in commands:
                    process_helm(command)

            workload_exists = DeployedWorkload.query.filter(
                DeployedWorkload.username == username,
                DeployedWorkload.workload_name == workload['type'],
                DeployedWorkload.duration == workload['duration'],
                DeployedWorkload.replicas == replicas,
                DeployedWorkload.node_name == workload['node_name'],
                DeployedWorkload.status == 'success',  # Ensure 'success' is correct
                DeployedWorkload.completed.is_(False),  # Correct way to check boolean
                DeployedWorkload.created_at == created_at
            ).first()

            if workload_exists:
                workload_exists.completed = True
                db.session.commit()

            logging.info(f"Workload '{workload['type']}' deleted successfully.")
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500


def get_cluster_nodes():
    load_kube_config()
    api_instance = kubernetes.client.CoreV1Api()
    nodes = api_instance.list_node()
    worker_nodes = [node.metadata.name for node in nodes.items if
                    "node-role.kubernetes.io/control-plane" not in node.metadata.labels]
    return worker_nodes


def delete_resources(workload_json, namespace):
    # Load Kubernetes configuration
    load_kube_config()
    k8s_client = client.ApiClient()
    dyn_client = dynamic.DynamicClient(k8s_client)

    # Parse all YAML files in the directory
    workload = workload_json.get("workload_name")
    directory = get_deployment_files_path(workload.lower())
    resource_defs = []

    for filename in os.listdir(directory):
        if filename.lower().endswith((".yaml", ".yml")):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as f:
                for doc in yaml.safe_load_all(f):
                    if doc and "kind" in doc and "metadata" in doc:
                        resource_defs.append(doc)

    # Delete resources defined in YAMLs
    for resource_def in resource_defs:
        api_version = resource_def.get("apiVersion", "v1")
        kind = resource_def.get("kind")
        metadata = resource_def.get("metadata", {})
        name = metadata.get("name")
        namespace = metadata.get("namespace", namespace)

        if not name:
            logging.info(f"Skipping resource {kind} with no name")
            continue

        try:
            # Get the dynamic API resource
            resource = dyn_client.resources.get(api_version=api_version, kind=kind)
        except Exception as e:
            logging.info(f"Error resolving API resource {kind} ({api_version}): {e}")
            continue

        try:
            # Check if resource is namespaced
            if resource.namespaced:
                logging.info(f"Deleting {kind}/{name} in namespace {namespace}")
                resource.delete(name=name, namespace=namespace)
            else:
                logging.info(f"Deleting cluster-scoped {kind}/{name}")
                resource.delete(name=name)
            time.sleep(5)
        except ApiException as e:
            if e.status == 404:
                logging.info(f"{kind} {name} not found (skipping)")
            else:
                logging.info(f"Failed to delete {kind} {name}: {str(e)}")


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
