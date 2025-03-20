import os


class Config:
    SECRET_KEY = 'admin_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
    KUBECONFIG_PATH = '/home/.kube/config'
    GRAFANA_URL = os.environ.get('GRAFANA_URL')
    GRAFANA_ADMIN_USER = os.environ.get('GRAFANA_ADMIN_USER')
    GRAFANA_ADMIN_PASSWORD = os.environ.get('GRAFANA_ADMIN_PASSWORD')
    PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL')
