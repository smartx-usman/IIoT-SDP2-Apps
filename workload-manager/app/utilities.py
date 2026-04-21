import logging
import re

from app import db
from app.grafana_manager import GrafanaManager
from app.kubernetes_utils import ensure_user_namespace
from app.models import User
from app.models import WorkloadType
from config import Config
from werkzeug.security import generate_password_hash

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def create_default_users():
    for user in ('admin', 'beginner', 'intermediate', 'advanced'):
        if not User.query.filter_by(username=user).first():
            quota_pods = 10
            quota_cpu = '2000m'
            quota_memory = '4Gi'
            if user == 'admin':
                hashed_password = generate_password_hash(password='admin_password', method='pbkdf2:sha256')
                new_user = User(username=user, password=hashed_password, role='admin', user_level='advanced',
                                quota_pods=quota_pods, quota_cpu=quota_cpu, quota_memory=quota_memory)
            else:
                hashed_password = generate_password_hash(password=user, method='pbkdf2:sha256')
                role = user
                if user[-1].isdigit():
                    role = user[:-1]
                new_user = User(username=user, password=hashed_password, role='user', user_level=role, quota_pods=quota_pods,
                                quota_cpu=quota_cpu, quota_memory=quota_memory)

                #namespace = f"user-{re.sub(r'[^a-z0-9-]', '', user.lower())[:45]}"
                namespace = f"{re.sub(r'[^a-z0-9-]', '', user.lower())[:45]}"
                ensure_user_namespace(username=user, namespace=namespace, quota_pods=quota_pods, quota_cpu=quota_cpu,
                                      quota_memory=quota_memory)

                grafana_mgr = GrafanaManager(
                    Config.GRAFANA_INTERNAL_URL,
                    Config.GRAFANA_ADMIN_USER,
                    Config.GRAFANA_ADMIN_PASSWORD,
                    verify_ssl=False
                )
                if not grafana_mgr.user_exists(user):
                    grafana_mgr.create_grafana_user(username=user)
                    # account_id, grafana_api_token = grafana_mgr.create_service_account(username=user)
                    # logging.info(f"Grafana Response: {account_id} - {grafana_api_token}")
                    #grafana_mgr.create_user_dashboard(user, namespace)

                    grafana_mgr.create_cluster_dashboard(user, namespace)
                    grafana_mgr.create_metrics_dashboard(user, namespace)
                    grafana_mgr.create_logs_dashboard(user, namespace)

            db.session.add(new_user)
            db.session.commit()
            logging.info(f'Action:Create Type:Default User:"{user}" Result:Success')


def create_experiment_users():
    for user in (
            'beginner1', 'beginner2', 'beginner3', 'beginner4', 'beginner5',
            'intermediate1', 'intermediate2', 'intermediate3', 'intermediate4', 'intermediate5',
            'advanced1', 'advanced2', 'advanced3', 'advanced4', 'advanced5'):
        if not User.query.filter_by(username=user).first():
            quota_pods = 10
            quota_cpu = '2000m'
            quota_memory = '4Gi'

            if user == 'admin':
                hashed_password = generate_password_hash(password='admin', method='pbkdf2:sha256')
                new_user = User(username=user, password=hashed_password, role='admin', user_level='advanced',
                                quota_pods=quota_pods, quota_cpu=quota_cpu, quota_memory=quota_memory)
            else:
                hashed_password = generate_password_hash(password=user, method='pbkdf2:sha256')
                role = user

                if user[-1].isdigit():
                    role = user[:-1]
                new_user = User(username=user, password=hashed_password, role='user', user_level=role, quota_pods=quota_pods,
                                quota_cpu=quota_cpu, quota_memory=quota_memory)

                namespace = f"{re.sub(r'[^a-z0-9-]', '', user.lower())[:45]}"
                ensure_user_namespace(username=user, namespace=namespace, quota_pods=quota_pods, quota_cpu=quota_cpu,
                                      quota_memory=quota_memory)

                grafana_mgr = GrafanaManager(
                    Config.GRAFANA_INTERNAL_URL,
                    Config.GRAFANA_ADMIN_USER,
                    Config.GRAFANA_ADMIN_PASSWORD
                )
                if not grafana_mgr.user_exists(user):
                    grafana_mgr.create_grafana_user(username=user)
                    # account_id, grafana_api_token = grafana_mgr.create_service_account(username=user)
                    # logging.info(f"Grafana Response: {account_id} - {grafana_api_token}")
                    grafana_mgr.create_metrics_dashboard(user, namespace)
                    grafana_mgr.create_logs_dashboard(user, namespace)


            db.session.add(new_user)
            db.session.commit()
            logging.info(f'Action:Create Type:Experiment User:"{user}" Result:Success')


def initialize_default_workloads():
    default_workloads = [
        {
            "name": "CoAP-Server",
            "deploy_method": "yaml"
        },
        {
            "name": "CPU-Burner",
            "deploy_method": "yaml"
        },
        {
            "name": "Disk-Burner",
            "deploy_method": "yaml"

        },
        {
            "name": "File-Server",
            "deploy_method": "yaml"
        },
        {
            "name": "Memory-Burner",
            "deploy_method": "yaml"
        },
        {
            "name": "Network-Burner",
            "deploy_method": "yaml"
        },
        {
            "name": "Mqtt-Broker",
            "deploy_method": "helm",
            "helm_repo_name": "t3n",
            "helm_repo_url": "https://storage.googleapis.com/t3n-helm-charts",
            "helm_chart": "mosquitto",
            "helm_chart_version": None,
            "helm_set_values": None
        },
        {
            "name": "Kafka-Broker",
            "deploy_method": "helm",
            "helm_repo_name": "bitnami",
            "helm_repo_url": "https://charts.bitnami.com/bitnami",
            "helm_chart": "kafka",
            "helm_chart_version": "31.1.0",
            "helm_set_values": None
        },
        {
            "name": "MySQL-Server",
            "deploy_method": "helm",
            "helm_repo_name": "bitnami",
            "helm_repo_url": "https://charts.bitnami.com/bitnami",
            "helm_chart": "mysql",
            "helm_chart_version": None,
            "helm_set_values": "primary.persistence.enabled=false"
        },
        {
            "name": "Data-Generator",
            "deploy_method": "yaml"
        },
        {
            "name": "Data-Publisher",
            "deploy_method": "yaml"
        },
        {
            "name": "Data-Subscriber",
            "deploy_method": "yaml"
        },
        {
            "name": "Data-Analyzer",
            "deploy_method": "yaml"
        },
        {
            "name": "Data-Actuator",
            "deploy_method": "yaml"
        },
        {
            "name": "Data-UI",
            "deploy_method": "yaml"
        },
    ]

    for workload in default_workloads:
        if not WorkloadType.query.filter_by(workload_name=workload['name']).first():
            if workload['deploy_method'] == 'yaml':
                new_workload = WorkloadType(workload_name=workload['name'], deploy_method='yaml', created_by='admin')
            else:
                new_workload = WorkloadType(workload_name=workload['name'],
                                            deploy_method='helm',
                                            workload_enabled=True,
                                            helm_repo_name=workload['helm_repo_name'],
                                            helm_repo_url=workload['helm_repo_url'],
                                            helm_chart=workload['helm_chart'],
                                            helm_chart_version=workload['helm_chart_version'],
                                            helm_set_values=workload.get('helm_set_values', None),
                                            created_by='admin')
            db.session.add(new_workload)
    db.session.commit()
