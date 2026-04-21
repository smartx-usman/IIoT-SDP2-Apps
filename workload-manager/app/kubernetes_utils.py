import logging
import os
import shutil
import subprocess
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps

import yaml
from app import create_app, db
from app.helm_utils import deploy_helm_workload
from app.models import HelmWorkload, YamlWorkload, DeployedWorkload
from app.workload_dir_finder import get_deployment_files_path
from config import Config
from flask import jsonify
from kubernetes.client.rest import ApiException

import kubernetes
from kubernetes import client, config, dynamic, utils


def log_workload_action(action, workload_type, namespace, status="Processing"):
    logging.info(f"Action:{action} Workload:{workload_type} Namespace:{namespace} Result:{status}")


def load_kube_config():
    try:
        kubernetes.config.load_kube_config(
            config_file=Config.KUBECONFIG_PATH)  # This looks for ~/.kube/config by default
    except kubernetes.config.ConfigException as e:
        logging.error(f"Could not load kube config: {e}")
        raise


def create_kubernetes_clients():
    load_kube_config()
    return (
        kubernetes.client.AppsV1Api(),
        kubernetes.client.BatchV1Api(),
        kubernetes.client.CoreV1Api()
    )


def create_namespace(api_instance_core, namespace_name):
    ns = kubernetes.client.V1Namespace(metadata=kubernetes.client.V1ObjectMeta(name=namespace_name))
    try:
        api_instance_core.create_namespace(ns)
        logging.info(f"Action:Create Namespace:{namespace_name} Result:Success")
    except ApiException as e:
        if e.status == 409:
            logging.info(f"Action:Create Namespace:{namespace_name} Result:Skip")
        else:
            logging.error(f"Action:Create Namespace:{namespace_name} Result:Error Trace:{e}")


def ensure_user_namespace(username, namespace, quota_pods, quota_cpu, quota_memory):
    load_kube_config()
    api = kubernetes.client.CoreV1Api()
    rbac_api = kubernetes.client.RbacAuthorizationV1Api()
    try:
        api.read_namespace(name=namespace)
        validate_resource_quota(namespace, quota_pods, quota_cpu, quota_memory)
        create_role(rbac_api, namespace)
        return True
    except ApiException as e:
        if e.status == 404:
            logging.info(f"Action:Create Namespace:{namespace} Result:Success")
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
                create_role(rbac_api, namespace)
            except ApiException as e:
                logging.error(f"Action:Create Namespace:{namespace} Result:Error Trace:{e}")
        else:
            logging.error(f"Action:Read Namespace:{namespace} Result:Error Trace:{e}")


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
            logging.info(f"Action:Create Namespace:{namespace} Quota:True Result:Success")
        else:
            logging.error(f"Action:Read Namespace:{namespace} Quota:True Result:Error Trace:{e}")
            raise


def create_role(api_instance, namespace, role_name="lifecycle-access-role"):
    role = client.V1Role(
        metadata=client.V1ObjectMeta(
            name=role_name,
            namespace=namespace
        ),
        rules=[
            client.V1PolicyRule(
                api_groups=["", "apps", "batch", "policy"],
                resources=[
                    "secrets", "serviceaccounts", "services", "configmaps",
                    "daemonsets", "deployments", "statefulsets", "jobs",
                    "poddisruptionbudgets"
                ],
                verbs=["create", "get", "list", "watch", "delete"]
            )
        ]
    )

    try:
        api_instance.create_namespaced_role(namespace=namespace, body=role)
        logging.info(f"Action:Create Namespace:{namespace} Role:{role_name} Result:Success")

        create_role_binding(api_instance, namespace, role_name, f"{role_name}-binding")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            logging.info(f"Action:Create Namespace:{namespace} Role:{role_name} Result:Skip")
            create_role_binding(api_instance, namespace, role_name, f"{role_name}-binding")
        else:
            logging.error(f"Action:Create Namespace:{namespace} Role:{role_name} Result:Error Trace:{e}")


def create_role_binding(api_instance, namespace, role_name, binding_name, sa_name="default", sa_namespace="simulation"):
    # Define the RoleBinding
    role_binding = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(
            name=binding_name,
            namespace=namespace
        ),
        subjects=[
            {
                "kind": "ServiceAccount",
                "name": sa_name,
                "namespace": sa_namespace
            }
        ],
        role_ref=client.V1RoleRef(
            kind="Role",
            name=role_name,
            api_group="rbac.authorization.k8s.io"
        )
    )

    # Create the RoleBinding
    try:
        api_instance.create_namespaced_role_binding(namespace=namespace, body=role_binding)
        logging.info(f"Action:Create Namespace:{namespace} RoleBinding:{binding_name} Result:Success")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            logging.info(f"Action:Create Namespace:{namespace} RoleBinding:{binding_name} Result:Skip")
        else:
            logging.error(f"Action:Create Namespace:{namespace} RoleBinding:{binding_name} Result:Error Trace:{e}")


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
        # doc['spec']['replicas'] = int(replicas)
        api_instance_apps.create_namespaced_deployment(namespace=namespace, body=doc)
    elif doc['kind'] == 'Job':
        api_instance_batch.create_namespaced_job(namespace=namespace, body=doc)
    elif doc['kind'] == 'ServiceAccount':
        api_instance_core.create_namespaced_service_account(namespace=namespace, body=doc)
    elif doc['kind'] == 'Service':
        api_instance_core.create_namespaced_service(namespace=namespace, body=doc)
    elif doc['kind'] == 'StatefulSet':
        api_instance_apps.create_namespaced_stateful_set(namespace=namespace, body=doc)
    elif doc['kind'] == 'Namespace':
        api_instance_core.create_namespace(body=doc)
    else:
        logging.warning(f"Action:Create Resource:{doc['kind']} Result:Skip")


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
        logging.warning(f"Action:Delete Resource:{doc['kind']} Result:Skip")


@contextmanager
def app_context():
    app = create_app()
    with app.app_context():
        yield app


def with_db_rollback(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            db.session.rollback()
            logging.error(f"Database operation failed in {func.__name__}: {e}")
            raise

    return wrapper


@with_db_rollback
def create_yaml_workload_record(workload, username, created_at):
    yaml_workload = YamlWorkload(
        replicas=int(workload.get('replicas', 1)),
        node_name=workload.get('node_name', 'any'),
    )
    db.session.add(yaml_workload)
    db.session.flush()

    new_workload = DeployedWorkload(
        username=username,
        workload_name=workload['type'],
        duration=int(workload['duration']),
        deployment_status='success',
        is_completed=False,
        created_at=created_at,
        yaml_workload_id=yaml_workload.id,
    )
    db.session.add(new_workload)
    db.session.flush()

    return new_workload


@with_db_rollback
def create_helm_workload_record(workload, username, created_at):
    helm_workload = HelmWorkload(
        chart_name=workload.get('chart_name'),
        chart_version=workload.get('chart_version'),
        set_values=workload.get('set_values'),
    )
    db.session.add(helm_workload)
    db.session.flush()

    new_workload = DeployedWorkload(
        username=username,
        workload_name=workload['type'],
        duration=int(workload['duration']),
        deployment_status='success',
        is_completed=False,
        created_at=created_at,
        helm_workload_id=helm_workload.id,
    )
    db.session.add(new_workload)
    db.session.flush()

    return new_workload


def extract_previous_workload_details(previous_workload):
    if not previous_workload:
        return None, None

    for row in previous_workload:
        if hasattr(row, 'yaml_workload') and row.yaml_workload:
            return row.yaml_workload.replicas, row.yaml_workload.node_name
    return None, None


def update_replicas_and_node_from_yaml(workload, deployment_dir, redeployment, previous_replicas, previous_node_name):
    if not redeployment:
        return workload

    yaml_files = [f for f in os.listdir(deployment_dir) if f.endswith(('.yaml', '.yml'))]
    if not yaml_files:
        return workload

    yaml_path = os.path.join(deployment_dir, yaml_files[0])

    # Update replicas if unchanged from previous
    if workload.get('replicas') == previous_replicas:
        yaml_info = extract_replicas_from_yaml(yaml_path)
        if yaml_info and 'replicas' in yaml_info:
            workload['replicas'] = yaml_info['replicas']

    # Update node name if unchanged from previous
    if workload.get('node_name') == previous_node_name:
        yaml_info = extract_node_selector_from_yaml(yaml_path)
        if yaml_info and 'nodeSelector' in yaml_info:
            node_selector = yaml_info['nodeSelector']
            workload['node_name'] = list(node_selector.values())[
                0] if node_selector and node_selector != "N/A" else 'any'

    return workload


def process_yaml_files(deployment_dir, namespace, workload, new_workload,
                       api_apps, api_batch, api_core, redeployment, previous_replicas, previous_node_name):
    resources = []
    replicas = int(workload.get('replicas', 1))

    for filename in os.listdir(deployment_dir):
        if not filename.endswith(('.yaml', '.yml')):
            continue

        file_path = os.path.join(deployment_dir, filename)
        with open(file_path, 'r') as file:
            for doc in yaml.safe_load_all(file):
                if not isinstance(doc, dict) or 'kind' not in doc:
                    continue

                # Update replicas if changed
                if not redeployment or (redeployment and replicas != previous_replicas):
                    if doc['kind'] in ['Deployment', 'StatefulSet']:
                        doc['spec']['replicas'] = replicas

                # Update node selector if changed
                if not redeployment or (redeployment and workload.get('node_name') != previous_node_name):
                    add_node_selector(doc, workload.get('node_name', 'any'))

                # Add workload_id label
                label_doc(doc, new_workload.workload_id)

                create_kubernetes_objects(
                    namespace=namespace,
                    doc=doc,
                    api_instance_apps=api_apps,
                    api_instance_core=api_core,
                    api_instance_batch=api_batch,
                    replicas=replicas
                )
                resources.append(doc)

    return resources


def handle_yaml_deployment(workload, username, namespace, deployment_dir,
                           redeployment, previous_workload, api_apps, api_batch, api_core):
    action = "Redeploy" if redeployment else "Create"
    log_workload_action(action, workload['type'], namespace, "Processing")

    # Extract previous details for redeployment
    previous_replicas, previous_node_name = extract_previous_workload_details(previous_workload)

    # Update workload with YAML data if needed
    workload = update_replicas_and_node_from_yaml(workload, deployment_dir, redeployment, previous_replicas, previous_node_name)

    # Create database records
    db_time = time.time()
    new_workload = create_yaml_workload_record(workload, username, datetime.utcnow())
    logging.info(f"Action:Measurement Function:create_yaml_workload_record Delay:{(time.time() - db_time) * 1000} ms")

    # Process YAML files
    #api_apps, api_batch, api_core = create_kubernetes_clients()
    resources = process_yaml_files(deployment_dir, namespace, workload, new_workload, api_apps, api_batch, api_core, redeployment, previous_replicas, previous_node_name)

    # Save YAML for history
    file_time = time.time()
    save_yaml_to_dir(resources, os.path.join(Config.UPLOAD_FOLDER, username, str(new_workload.workload_id)), f"{workload['type'].lower()}.yaml")
    logging.info(f"Action:Measurement Function:save_yaml_to_dir Delay:{(time.time() - file_time) * 1000} ms")

    db.session.commit()
    log_workload_action(action, workload['type'], namespace, "Success")

    return new_workload, resources #, api_apps, api_batch, api_core


def handle_helm_deployment(workload, username, namespace, deployment_dir,
                           redeployment, previous_workload_id):
    """Handle Helm-based Kubernetes deployment."""
    action = "Redeploy" if redeployment else "Create"
    log_workload_action(action, workload['type'], namespace, "Processing")

    # Create database records
    new_workload = create_helm_workload_record(workload, username, datetime.utcnow())

    # Deploy Helm chart
    result, result_code = deploy_helm_workload(
        new_workload.workload_id, workload, username, namespace,
        redeployment, previous_workload_id
    )

    if result_code != 200:
        raise RuntimeError(f"Helm deployment failed for {workload['type']}")

    # Copy deployment files for history
    experiment_dir = os.path.join(Config.UPLOAD_FOLDER, username, str(new_workload.workload_id))
    os.makedirs(experiment_dir, exist_ok=True)

    source_dir = deployment_dir if redeployment else get_deployment_files_path(workload['type'].lower(), username)
    for file in os.listdir(source_dir):
        shutil.copy2(os.path.join(source_dir, file), experiment_dir)

    db.session.commit()
    log_workload_action(action, workload['type'], namespace, "Success")

    return new_workload


def wait_and_cleanup(workload, namespace, cleanup_func, new_workload, *cleanup_args):
    time.sleep(int(workload['duration']))

    # logging.info(f"Action:Delete Workload:{workload['type']} Namespace:{namespace} Result:Processing")
    log_workload_action("Delete", workload['type'], namespace, "Processing")

    cleanup_func(*cleanup_args)
    update_workload_status(new_workload.workload_id)

    # logging.info(f"Action:Delete Workload:'{workload['type']}' Namespace:{namespace} Result:Success")
    log_workload_action("Delete", workload['type'], namespace, "Success")


def cleanup_yaml_resources(resources, namespace, api_apps, api_core, api_batch):
    for resource in resources:
        try:
            delete_kubernetes_objects(
                namespace=namespace,
                doc=resource,
                api_instance_apps=api_apps,
                api_instance_core=api_core,
                api_instance_batch=api_batch
            )
        except ApiException as e:
            if e.status != 404:  # Ignore not found errors
                logging.error(
                    f"Action:Delete Kind:{resource['kind']} "
                    f"Name:{resource['metadata']['name']} "
                    f"Namespace:{namespace} Trace:{e}"
                )


def wait_and_cleanup(workload, namespace, cleanup_func, new_workload, *cleanup_args):
    time.sleep(int(workload['duration']))

    logging.info(f"Action:Delete Workload:{workload['type']} Namespace:{namespace} Result:Processing")

    cleanup_func(*cleanup_args)
    update_workload_status(new_workload.workload_id)

    logging.info(f"Action:Delete Workload:'{workload['type']}' Namespace:{namespace} Result:Success")


def manage_kubernetes_resources(workload, username, namespace, redeployment=False,
                                previous_workload_id=None, previous_workload=None):
    app = create_app()
    with app.app_context():
        api_apps, api_batch, api_core = create_kubernetes_clients()
        deploy_method = workload.get('deploy_method', 'yaml')
        deployment_dir = os.path.join(Config.UPLOAD_FOLDER, username,
                                      str(previous_workload_id)) if redeployment else get_deployment_files_path(
            workload['type'].lower(), username)

        try:
            if deploy_method == 'yaml':
                new_workload, resources = handle_yaml_deployment(workload, username, namespace, deployment_dir, redeployment, previous_workload, api_apps, api_batch, api_core)

                wait_and_cleanup(workload, namespace, cleanup_yaml_resources, new_workload,resources, namespace, api_apps, api_core, api_batch)

            elif deploy_method == 'helm':
                new_workload = handle_helm_deployment(workload, username, namespace, deployment_dir, redeployment, previous_workload_id)

                wait_and_cleanup(workload, namespace,
                    lambda: subprocess.run([f'helm delete {workload["type"].lower()} --kubeconfig {Config.KUBECONFIG_PATH} -n {namespace}'], check=True,shell=True),
                    new_workload
                )
            #return jsonify({"status": "success"}), 200
        except Exception as e:
            logging.error(f"Workload '{workload['type']}' failed: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    #return jsonify({"status": "success"}), 200


def handle_workloads(workloads, redeployment=False, username=None, namespace=None, previous_workload_id=None,
                     previous_workload=None):
    for workload in workloads:
        start = time.time()
        threading.Thread(target=manage_kubernetes_resources,
                         args=(workload, redeployment, username, namespace, previous_workload_id, previous_workload)
                         ).start()
        logging.info(f"Action:Measurement Function:manage_kubernetes_resources Delay:{(time.time() - start) * 1000} ms")
        time.sleep(5)


def manage_kubernetes_resources_(workload, username, namespace, redeployment=False, previous_workload_id=None,
                                 previous_workload=None):
    app = create_app()
    created_at = datetime.utcnow()
    deploy_method = workload.get('deploy_method', 'yaml')

    with app.app_context():  # Manually push the application context
        api_apps, api_batch, api_core = create_kubernetes_clients()

        previous_replicas = None
        previous_node_name = None

        deployment_dir = os.path.join(Config.UPLOAD_FOLDER, username,
                                      str(previous_workload_id)) if redeployment else get_deployment_files_path(
            workload['type'].lower(), username)

        if redeployment:
            logging.info(f"Action:Redeploy Workload:{workload['type']} Namespace:{namespace} Result: Processing")
        else:
            logging.info(f"Action:Create Workload:{workload['type']} Namespace:{namespace} Result: Processing")

        try:
            if deploy_method == 'yaml':
                replicas = int(workload.get('replicas', 1))

                # Add logic to ensure the replicas and node_name are valid in the database
                if redeployment:
                    # logging.info('Redeployment detected, checking previous workload details...')
                    yaml_files = [f for f in os.listdir(deployment_dir) if f.endswith(('.yaml', '.yml'))]
                    if yaml_files:
                        # Check if Edit and Redeploy is invoked
                        for row in previous_workload:
                            previous_replicas = row.yaml_workload.replicas
                            previous_node_name = row.yaml_workload.node_name

                        # logging.info(
                        #    f'Previous replicas: {previous_replicas}, Previous node name: {previous_node_name} Current replicas: {replicas}, Current node name: {workload["node_name"]}')

                        if replicas == previous_replicas:
                            info = extract_replicas_from_yaml(os.path.join(deployment_dir, yaml_files[0]))
                            # logging.info(f'Condition met. Replicas from YAML: {info.get("replicas")}')
                            if info:
                                replicas = int(info['replicas'])

                        if workload['node_name'] == previous_node_name:
                            info = extract_node_selector_from_yaml(os.path.join(deployment_dir, yaml_files[0]))
                            # logging.info(f'Node selector from YAML: {info.get("nodeSelector")}')
                            if info:
                                if info['nodeSelector'] and info['nodeSelector'] != "N/A":
                                    # workload['node_name'] = list(info['nodeSelector'].keys())[0]
                                    workload['node_name'] = list(info['nodeSelector'].values())[0]
                                else:
                                    workload['node_name'] = 'any'
                # logging.info(f'Replicas: {replicas}, Node Name: {workload["node_name"]}')

                yaml_workload = YamlWorkload(
                    replicas=replicas,
                    node_name=workload['node_name'],
                )
                db.session.add(yaml_workload)
                db.session.flush()

                new_workload = DeployedWorkload(
                    username=username,
                    workload_name=workload['type'],
                    duration=int(workload['duration']),
                    deployment_status='success',
                    is_completed=False,
                    created_at=created_at,
                    yaml_workload_id=yaml_workload.id,
                )

                db.session.add(new_workload)
                db.session.flush()

                resources = []
                for filename in os.listdir(deployment_dir):
                    if filename.endswith('.yaml' or '.yml'):
                        with open(os.path.join(deployment_dir, filename), 'r') as file:
                            for doc in yaml.safe_load_all(file):
                                if not isinstance(doc, dict) or 'kind' not in doc:
                                    continue

                                # Ensure this is not a redeployment
                                if not redeployment or (redeployment and replicas != previous_replicas):
                                    if doc['kind'] in ['Deployment', 'StatefulSet']:
                                        doc['spec']['replicas'] = int(replicas)

                                if not redeployment or (redeployment and workload['node_name'] != previous_node_name):
                                    # logging.info(
                                    #    f'Previous node name: {previous_node_name}, Current node name: {workload["node_name"]}')
                                    add_node_selector(doc, workload['node_name'])

                                # Add workload_id label to enable Grafana filtering
                                label_doc(doc, new_workload.workload_id)

                                create_kubernetes_objects(
                                    namespace=namespace,
                                    doc=doc,
                                    api_instance_apps=api_apps,
                                    api_instance_core=api_core,
                                    api_instance_batch=api_batch,
                                    replicas=replicas
                                )
                                resources.append(doc)

                # Create a directory for the workload history and redeployments
                save_yaml_to_dir(resources, os.path.join(Config.UPLOAD_FOLDER, username, str(new_workload.workload_id)),
                                 f"{workload['type'].lower()}.yaml")
                db.session.commit()

                if redeployment:
                    logging.info(f"Action:Redeploy Workload:{workload['type']} Namespace:{namespace} Result:Success")
                else:
                    logging.info(f"Action:Create Workload:'{workload['type']}' Namespace:{namespace} Result:Success")

                # time.sleep(int(workload['duration']))
                # logging.info(f"Action: Delete Workload: {workload['type']} Namespace:{namespace} Result: Processing")

                # for resource in resources:
                #     try:
                #         delete_kubernetes_objects(namespace=namespace,
                #                                   doc=resource,
                #                                   api_instance_apps=api_apps,
                #                                   api_instance_core=api_core,
                #                                   api_instance_batch=api_batch)
                #
                #     except ApiException as e:
                #         if e.status != 404:
                #             logging.error(
                #                 f"Action:Delete Kind:{resource['kind']} Name:{resource['metadata']['name']} Namespace:{namespace} Trace:{e}")
                #
                # update_workload_status(new_workload.workload_id)
                #
                # logging.info(f"Action:Delete Workload:'{workload['type']}' Namespace:{namespace} Result:Success")

            if deploy_method == 'helm':
                helm_workload = HelmWorkload(
                    chart_name=workload.get('chart_name'),
                    chart_version=workload.get('chart_version'),
                    set_values=workload.get('set_values'),
                )
                db.session.add(helm_workload)
                db.session.flush()  # Get the ID of the newly created helm_workload

                new_workload = DeployedWorkload(
                    username=username,
                    workload_name=workload['type'],
                    duration=workload['duration'],
                    deployment_status='success',
                    is_completed=False,
                    created_at=created_at,
                    helm_workload_id=helm_workload.id,  # Associate with Helm workload
                )

                db.session.add(new_workload)
                db.session.flush()

                result, result_code = deploy_helm_workload(new_workload.workload_id, workload, username, namespace,
                                                           redeployment, previous_workload_id)

                if result_code == 200:
                    # Create a directory for the workload history and redeployments
                    experiment_dir = os.path.join(Config.UPLOAD_FOLDER, username, str(new_workload.workload_id))
                    os.makedirs(experiment_dir, exist_ok=True)
                    source_dir = deployment_dir if redeployment else get_deployment_files_path(workload['type'].lower(),
                                                                                               username)

                    for file in os.listdir(source_dir):
                        shutil.copy2(os.path.join(source_dir, file), experiment_dir)

                    db.session.commit()
                    time.sleep(int(workload['duration']))

                    logging.info(
                        f"Action: Delete Workload: {workload['type']} Namespace:{namespace} Result: Processing")

                    subprocess.run(
                        [f'helm delete {workload["type"].lower()} --kubeconfig {Config.KUBECONFIG_PATH} -n {namespace}'],
                        check=True,
                        shell=True
                    )

                    update_workload_status(new_workload.workload_id)

                    logging.info(f"Action:Delete Workload:'{workload['type']}' Namespace:{namespace} Result:Success\n")

                else:
                    db.session.rollback()
                    raise RuntimeError(f"Helm deployment failed for {workload['type']}")

        except Exception as e:
            db.session.rollback()
            logging.error(f"Workload '{workload['type']}' failed: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500


def extract_replicas_from_yaml(path):
    try:
        with open(path, 'r') as f:
            info = {
                'replicas': None,
            }
            for doc in yaml.safe_load_all(f):
                kind = doc.get('kind')

                if isinstance(doc, dict) and doc.get('kind') in ['Deployment', 'StatefulSet', 'Job']:
                    info['replicas'] = doc.get('spec', {}).get('replicas', 1)
            return info
    except yaml.YAMLError as e:
        logging.error(f"YAML error in {path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error reading {path}: {e}")
        raise Exception(f"Failed to read YAML file: {e}")
    # return 1


def extract_node_selector_from_yaml(path):
    try:
        with open(path, 'r') as f:
            info = {
                'nodeSelector': None
            }
            for doc in yaml.safe_load_all(f):
                kind = doc.get('kind')

                if kind == 'Deployment' or kind == 'StatefulSet':
                    node_selector = doc.get('spec', {}).get('template', {}).get('spec', {}).get('nodeSelector')
                    if isinstance(node_selector, dict):
                        info['nodeSelector'] = node_selector
                elif kind == 'Job':
                    node_selector = doc.get('spec', {}).get('template', {}).get('spec', {}).get('nodeSelector')
                    if isinstance(node_selector, dict):
                        info['nodeSelector'] = node_selector
                elif kind == 'Pod':
                    node_selector = doc.get('spec', {}).get('nodeSelector')
                    if isinstance(node_selector, dict):
                        info['nodeSelector'] = node_selector
                else:
                    info['nodeSelector'] = 'N/A'

            return info
    except yaml.YAMLError as e:
        logging.error(f"YAML error in {path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error reading {path}: {e}")
        raise Exception(f"Failed to read YAML file: {e}")


def add_node_selector(doc, node_name):
    if node_name == 'any':
        if doc['kind'] == 'Pod':
            node_selector = doc.get('spec', {}).get('nodeSelector', {})
            if 'kubernetes.io/hostname' in node_selector:
                del doc['spec']['nodeSelector']['kubernetes.io/hostname']
        elif doc['kind'] in ['Deployment', 'StatefulSet', 'Job']:
            node_selector = doc.get('spec', {}).get('template', {}).get('spec', {}).get('nodeSelector', {})
            if 'kubernetes.io/hostname' in node_selector:
                del doc['spec']['template']['spec']['nodeSelector']['kubernetes.io/hostname']
        else:
            logging.warning(f"Unsupported kind: {doc['kind']}")
        return

    if doc['kind'] == 'Pod':
        doc.setdefault('spec', {}).setdefault('nodeSelector', {})['kubernetes.io/hostname'] = node_name
    elif doc['kind'] in ['Deployment', 'StatefulSet', 'Job']:
        doc.setdefault('spec', {}).setdefault('template', {}).setdefault('spec', {}).setdefault('nodeSelector', {})[
            'kubernetes.io/hostname'] = node_name
    else:
        logging.warning(f"Unsupported kind: {doc['kind']}")
        return


def label_doc(doc, workload_id):
    if doc['kind'] == 'Pod':
        doc.setdefault('metadata', {}).setdefault('labels', {})['workload_id'] = str(workload_id)
    elif doc['kind'] in ['Deployment', 'StatefulSet', 'Job']:
        doc['spec']['template'].setdefault('metadata', {}).setdefault('labels', {})['workload_id'] = str(workload_id)


def save_yaml_to_dir(resources, experiment_dir, yaml_file_name):
    os.makedirs(experiment_dir, exist_ok=True)
    try:
        with open(os.path.join(experiment_dir, yaml_file_name), 'w') as f:
            yaml.safe_dump_all(resources, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        logging.error(f"Error saving YAML to file {experiment_dir}/{yaml_file_name}: {e}")
        raise RuntimeError(f"Failed to write YAML: {e}")


def update_workload_status(workload_id):
    workload_exists = DeployedWorkload.query.filter(
        DeployedWorkload.workload_id == workload_id,
        DeployedWorkload.is_completed.is_(False),  # Correct way to check boolean
    ).first()

    if workload_exists:
        workload_exists.is_completed = True
        workload_exists.finished_at = datetime.utcnow()
        db.session.commit()


def get_cluster_nodes():
    load_kube_config()
    api_instance = kubernetes.client.CoreV1Api()
    nodes = api_instance.list_node()
    worker_nodes = [node.metadata.name for node in nodes.items if
                    "node-role.kubernetes.io/control-plane" not in node.metadata.labels]
    return worker_nodes


def process_helm(command):
    subprocess.run(command, check=True, shell=True)


def delete_resources(workload_json, namespace, username):
    # Load Kubernetes configuration
    load_kube_config()
    k8s_client = client.ApiClient()
    dyn_client = dynamic.DynamicClient(k8s_client)
    workload_id = workload_json.get("workload_id")
    workload = workload_json.get("workload_name")

    deploy_method = workload_json.get("deploy_method", "yaml")
    deployment_dir = get_deployment_files_path(workload.lower(), username)
    resource_defs = []

    if deploy_method == "helm":
        try:
            command = [f'helm delete {workload.lower()} --kubeconfig {Config.KUBECONFIG_PATH} -n {namespace}']
            process_helm(command)
            update_workload_status(workload_id)
        except Exception as e:
            logging.error(
                f"Action:Delete Method:{deploy_method} Workload:{workload}: Namespace:{namespace} Trace:{str(e)}")

    else:
        for filename in os.listdir(deployment_dir):
            if filename.lower().endswith((".yaml", ".yml")):
                filepath = os.path.join(deployment_dir, filename)
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
                logging.error(f"Error resolving API resource {kind} ({api_version}): {e}")
                continue

            try:
                # Check if resource is namespaced
                if resource.namespaced:
                    resource.delete(name=name, namespace=namespace)
                else:
                    resource.delete(name=name)
                time.sleep(5)
            except ApiException as e:
                if e.status == 404:
                    logging.info(f"{kind} {name} not found (skipping)")
                else:
                    logging.info(f"Failed to delete {kind} {name}: {str(e)}")

        update_workload_status(workload_id)
