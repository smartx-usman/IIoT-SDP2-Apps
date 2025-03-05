import uuid
from datetime import datetime
import re

from app import db
from flask_login import UserMixin


# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'
    user_level = db.Column(db.String(15), nullable=False, default='beginner')  # 'beginner', 'intermediate', 'advanced'
    namespace = db.Column(db.String(50), unique=True, nullable=False)
    quota_pods = db.Column(db.Integer, nullable = False, default = 2)
    quota_cpu = db.Column(db.String(15), nullable=False, default='1000m')  # In millicores
    quota_memory = db.Column(db.String(15), nullable=False, default='1Gi')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.namespace = self.generate_namespace()

    def generate_namespace(self):
        clean_ns = re.sub(r'[^a-z0-9-]', '', self.username.lower())[:45]
        #return f"user-{clean_ns}-{uuid.uuid4().hex[:4]}"

        return f"user-{clean_ns}"


class DeployedWorkload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    workload_name = db.Column(db.String(255), db.ForeignKey('workload_type.workload_name'), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    replicas = db.Column(db.Integer, nullable=False)
    node_name = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')
    completed = db.Column(db.Boolean, nullable=True, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user = db.relationship('User')
    workload_type = db.relationship('WorkloadType')


class WorkloadType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workload_name = db.Column(db.String(255), unique=True, nullable=False)
    workload_enabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    deploy_method = db.Column(db.String(50), nullable=False, default='yaml')
    user = db.relationship('User')
    created_by = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)


class HelmDeployment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    release_name = db.Column(db.String(255), nullable=False)
    chart = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(50))
    repo_url = db.Column(db.String(255))
    values_files = db.Column(db.Text)  # JSON list of stored values files
    set_values = db.Column(db.Text)  # JSON key-value pairs
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
