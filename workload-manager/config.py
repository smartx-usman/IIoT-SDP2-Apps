import os


class Config:
    SECRET_KEY = 'admin_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
    KUBECONFIG_PATH = '/home/.kube/config'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
    GRAFANA_INTERNAL_URL = os.environ.get('GRAFANA_INTERNAL_URL')
    GRAFANA_PUBLIC_URL = os.environ.get('GRAFANA_PUBLIC_URL')
    GRAFANA_ADMIN_USER = os.environ.get('GRAFANA_ADMIN_USER')
    GRAFANA_ADMIN_PASSWORD = os.environ.get('GRAFANA_ADMIN_PASSWORD')
