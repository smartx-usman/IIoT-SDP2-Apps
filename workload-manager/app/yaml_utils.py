import logging
import os

import yaml
from ruamel.yaml import YAML
from app import db
from app.models import WorkloadType
from config import Config
from flask import jsonify


def handle_yaml_deployment(request, user_level):
    try:
        config_method = request.form.get('config_method')
        logging.info(f"Config method: {config_method}")

        if config_method == 'upload':
            # yaml_file = request.files['yaml_file']
            # Validate and process uploaded YAML
            return handle_yaml_upload(request)

        elif config_method == 'dynamic':
            # Validate based on user level
            #if user_level == 'beginner' and not validate_beginner_fields(request.form):
            #    return jsonify({"status": "error", "message": "Missing required fields"}), 400

            # Generate YAML dynamically
            yaml_content = generate_yaml_from_form(request.form, user_level)

            logging.info(f"Generated YAML: {yaml_content}")
            return handle_dynamic_yaml(request, yaml_content)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def handle_yaml_upload(request):
    try:
        workload_name = request.form.get('workload_name')
        workload_enabled = request.form.get('workload_enabled', 'true').lower() == 'true'
        files = request.files.getlist('files')

        # Check if workload type already exists
        if WorkloadType.query.filter_by(workload_name=workload_name).first():
            return jsonify(status='error', message='Workload with same name already exists'), 400

        # Create new workload type
        new_workload = WorkloadType(
            workload_name=workload_name,
            workload_enabled=workload_enabled
        )
        db.session.add(new_workload)
        db.session.commit()

        # Create directory using ID
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, str(new_workload.workload_name))
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            if file and file.filename.endswith(('.yaml', '.yml')):
                file.save(os.path.join(upload_dir, file.filename))

        return jsonify({"status": "success", "message": "Workload type added successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


def generate_yaml_from_form(form_data, user_level):
    name = form_data.get('workload_name').lower().replace(' ', '-')
    replicas = form_data.get('replicas')
    image = form_data.get('container_image')
    container_port = form_data.get('container_port')
    cmd_interpreter = form_data.get('cmd_interpreter')
    cmd_arguments = form_data.get('cmd_arguments')

    base_spec = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name},
        "spec": {
            "replicas": int(replicas),
            "selector": {
                "matchLabels": {
                    "app": name
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": name
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": name,
                            "image": image,
                            "ports": [{"containerPort": int(container_port)}],
                            "command": [cmd_interpreter],
                            "args": [cmd_arguments]
                        }
                    ]
                }
            },
        },
    }

    if user_level in ['intermediate', 'advanced']:
        base_spec['spec']['template']['spec']['containers'][0]['resources'] = {
            'limits': {
                'cpu': f"{form_data['cpu_limit']}",
                'memory': f"{form_data['memory_limit']}Mi"
            }
        }

    if user_level == 'advanced':
        if form_data['affinity']:
            base_spec['spec']['template']['spec']['affinity'] = yaml.safe_load(form_data['affinity'])
        if form_data['tolerations']:
            base_spec['spec']['template']['spec']['tolerations'] = yaml.safe_load(form_data['tolerations'])

    return base_spec


def handle_dynamic_yaml(request, data):
    try:
        workload_name = request.form.get('workload_name')
        workload_enabled = request.form.get('workload_enabled', 'true').lower() == 'true'

        # Check if workload type already exists
        if WorkloadType.query.filter_by(workload_name=workload_name).first():
            return jsonify(status='error', message='Workload with same name already exists'), 400

        # Create new workload type
        new_workload = WorkloadType(
            workload_name=workload_name,
            workload_enabled=workload_enabled
        )

        # Create directory using ID
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, str(new_workload.workload_name))
        os.makedirs(upload_dir, exist_ok=True)

        yaml = YAML()
        yaml.indent(sequence=4, offset=2)
        yaml.preserve_quotes = True

        with open(os.path.join(upload_dir, "deployment.yaml"), "w") as file_handler:
            yaml.dump(data, file_handler)

        db.session.add(new_workload)
        db.session.commit()

        return jsonify({"status": "success", "message": "Workload type added successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


def validate_beginner_fields(form_data):
    required = ['name', 'image', 'replicas', 'port']
    return all(form_data.get(field) for field in required)


def validate_advanced_yaml(yaml_content):
    try:
        # Add schema validation here
        parsed = yaml.safe_load(yaml_content)
        return True
    except Exception as e:
        return False
