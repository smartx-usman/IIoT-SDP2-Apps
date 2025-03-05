import os


class Config:
    SECRET_KEY = 'admin_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
    KUBECONFIG_PATH = '/home/.kube/config'
