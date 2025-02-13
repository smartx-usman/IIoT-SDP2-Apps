import os


class Config:
    SECRET_KEY = 'admin_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
    WORKLOADS_NAMESPACE = os.environ.get('WORKLOADS_NAMESPACE', 'default')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
    KUBECONFIG_PATH = '/home/.kube/config'
    WORKLOAD_TYPES_FILE = '/mnt/data/workload_types.json'
    USER_LEVEL_CONFIG = {
        'beginner': {
            'fields': ['image', 'replicas', 'port'],
            'show_advanced': False
        },
        'intermediate': {
            'fields': ['image', 'replicas', 'port', 'cpu_limit', 'memory_limit', 'node_selector'],
            'show_advanced': False
        },
        'advanced': {
            'fields': ['image', 'replicas', 'port', 'cpu_limit', 'memory_limit',
                       'node_selector', 'affinity', 'tolerations', 'liveness_probe'],
            'show_advanced': True
        }
    }
