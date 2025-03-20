import logging
import os
import time

import yaml
from flask import Blueprint, jsonify, request, make_response, Response, session, render_template, stream_with_context
from flask_login import login_required, current_user
from app.kubernetes_utils import load_kube_config, process_helm, create_kubernetes_objects
import kubernetes
from kubernetes.client.rest import ApiException
from app.kubernetes_utils import create_namespace
from config import Config

monitoring_bp = Blueprint('monitoring', __name__)


@monitoring_bp.route('/monitoring', methods=['POST'])
@login_required
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
            commands = ['helm repo add prometheus-community https://prometheus-community.github.io/helm-charts',
                        'helm repo add grafana https://grafana.github.io/helm-charts',
                        f'helm -n {namespace} upgrade --install prometheus --kubeconfig {Config.KUBECONFIG_PATH} -f {deployment_dir}/prometheus.yaml prometheus-community/prometheus'
                        f'helm -n {namespace} upgrade --install grafana --kubeconfig {Config.KUBECONFIG_PATH} -f {deployment_dir}/grafana.yaml grafana/grafana'
                        ]

            for command in commands:
                process_helm(command, 'install')

            time.sleep(15)

            files = ['telegraf-serviceaccount.yaml', 'telegraf.yaml']

            for filename in files:
                logging.info(f"Deploying {filename}")
                with open(os.path.join(deployment_dir, filename), 'r') as file:
                    documents = yaml.safe_load_all(file)
                    for doc in documents:
                        create_kubernetes_objects(namespace=namespace,
                                                  doc=doc,
                                                  api_instance_apps=api_instance_apps,
                                                  api_instance_core=api_instance_core,
                                                  api_instance_rbac=api_instance_rbac)

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

        return jsonify(
            {"status": "success", "message": f"Monitoring system {selected_option} request submitted successfully."})
    except Exception as e:
        logging.error(str(e))
        return jsonify({"status": "error", "message": str(e)})


#@monitoring_bp.route('/grafana_proxy/<path:subpath>')
#@login_required
#def grafana_proxy(subpath):
    ##full_url = f"{Config.GRAFANA_URL}/d/{current_user.namespace}/user-dashboard-{current_user.username}"
    #full_url = f"{Config.GRAFANA_URL}/{subpath}"

    #logging.info(f"Proxying request to Grafana: {full_url}")

    #grafana_session = session.get("grafana_cookies")
    #logging.info(f"Grafana session cookies: {grafana_session}")
    #logging.info(f"Request Client IP: {request.remote_addr} - Request Host: {request.host} - User-Agent: {request.headers.get('User-Agent')}")


