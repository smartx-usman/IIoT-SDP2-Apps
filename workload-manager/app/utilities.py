import logging
import json
import os
from app import db
from app.models import User
from app.models import WorkloadType
from werkzeug.security import generate_password_hash

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def create_default_admin():
    if not User.query.filter_by(role='admin').first():
        hashed_password = generate_password_hash('admin_password', method='pbkdf2:sha256')
        new_admin = User(username='admin', password=hashed_password, role='admin', user_level='advanced')
        db.session.add(new_admin)
        db.session.commit()
        logging.info(f'Default admin user created. Username: admin, Password: admin_password')


def initialize_default_workloads():
    default_workloads = [
        "CoAP-Server-App",
        "CPU-Burner",
        "Disk-Burner",
        "File-Server-App",
        "IoT-Sensor-Data-Processing-App",
        "Memory-Burner",
        "Network-Burner",
        "Web-Server-App",
    ]

    for name in default_workloads:
        if not WorkloadType.query.filter_by(workload_name=name).first():
            new_workload = WorkloadType(workload_name=name)
            db.session.add(new_workload)
    db.session.commit()

# ... add other utility functions as needed ...
