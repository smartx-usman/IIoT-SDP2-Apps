import logging
import re

from app import db
from app.models import User
from app.models import WorkloadType
from werkzeug.security import generate_password_hash
from app.kubernetes_utils import ensure_user_namespace
from app.grafana_manager import GrafanaManager
from config import Config

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def create_default_users():
    for user in ('admin', 'beginner', 'intermediate', 'advanced'):
        if not User.query.filter_by(username=user).first():
            if user == 'admin':
                hashed_password = generate_password_hash(password='admin_password', method='pbkdf2:sha256')
                new_user = User(username=user, password=hashed_password, role='admin', user_level='advanced', quota_pods=10, quota_cpu='4000m', quota_memory='16Gi')
            else:
                hashed_password = generate_password_hash(password=user, method='pbkdf2:sha256')
                new_user = User(username=user, password=hashed_password, role='user', user_level=user, quota_pods=10, quota_cpu='2000m', quota_memory='4Gi')

                namespace = f"user-{re.sub(r'[^a-z0-9-]', '', user.lower())[:45]}"
                ensure_user_namespace(username=user, namespace=namespace, quota_pods=10, quota_cpu='2000m', quota_memory='4Gi')

                grafana_mgr = GrafanaManager(
                    Config.GRAFANA_URL,
                    Config.GRAFANA_ADMIN_USER,
                    Config.GRAFANA_ADMIN_PASSWORD
                )
                if not grafana_mgr.user_exists(user):
                    grafana_mgr.create_grafana_user(username=user)
                    #account_id, grafana_api_token = grafana_mgr.create_service_account(username=user)
                    #logging.info(f"Grafana Response: {account_id} - {grafana_api_token}")
                    grafana_mgr.create_user_dashboard(user, namespace)

            db.session.add(new_user)
            db.session.commit()
            logging.info(f'Default user: "{user}" account created.')


def initialize_default_workloads():
    default_workloads = [
        "CoAP-Server",
        "CPU-Burner",
        "Disk-Burner",
        "File-Server",
        "IoT-Sensor-Pipeline",
        "Memory-Burner",
        "Network-Burner",
        "Web-Server",
    ]

    for name in default_workloads:
        if not WorkloadType.query.filter_by(workload_name=name).first():
            new_workload = WorkloadType(workload_name=name, created_by='admin')
            db.session.add(new_workload)
    db.session.commit()
