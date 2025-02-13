from datetime import datetime

from app import db
from flask_login import UserMixin

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'
    user_level = db.Column(db.String(15), nullable=False, default='beginner')  # 'beginner', 'intermediate', 'advanced'


class DeployedWorkload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    workload_name = db.Column(db.String(255), db.ForeignKey('workload_type.workload_name'), nullable=False)
    #workload_name = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    replicas = db.Column(db.Integer, nullable=False)
    node_name = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    #updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    #yaml_content = db.Column(db.Text, nullable=True)
    user = db.relationship('User')
    #workload_type_id = db.Column(db.Integer, db.ForeignKey('workload_type.id'), nullable=False)
    workload_type = db.relationship('WorkloadType')

class WorkloadType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #workload_key = db.Column(db.String(150), unique=True, nullable=False)
    workload_name = db.Column(db.String(255), unique=True, nullable=False)
    workload_enabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)