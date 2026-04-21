import logging
import os
import subprocess
from datetime import datetime

from app import create_app, db
from app.models import DeployedWorkload, User, WorkloadType, HelmDeployment
from app.workload_dir_finder import get_deployment_files_path
from config import Config
from flask import jsonify


def add_helm_type_workload(request, user):
    deploy_method = request.form.get('deployMethod')
    workload_name = request.form.get('workloadDisplayName').lower().replace(' ', '-')
    workload_enabled = request.form.get('workload_enabled', 'true').lower() == 'true'
    repo_name = request.form.get('helm_repo_name')
    repo_url = request.form.get('helm_repo_url')
    chart_name = request.form.get('helm_chart_name')
    chart_version = request.form.get('helm_chart_version')
    values = request.form.get('helm_set_values')
    # file = request.files.get('helm_values_file')

    files = []

    if request.files and 'helm_file' in request.files:
    #if 'helm_file' in request.files:
        files = request.files.getlist('helm_file')

    try:
        # Check if workload template with the same name already exists
        query = WorkloadType.query.filter(
            WorkloadType.created_by == user.username,
            WorkloadType.workload_name == workload_name
        ).first()

        logging.info(f"Checking for existing workload with name: {workload_name}")

        # if WorkloadType.query.filter_by(workload_name=workload_name).first():
        if query:
            logging.error(f"Workload with the same name {workload_name} already exists")
            return jsonify(status='error', message='Workload with same name already exists'), 400

        # Create directory and upload file
        upload_dir = get_deployment_files_path(str(workload_name), user.username)
        os.makedirs(upload_dir, exist_ok=True)

        if not files or files[0].filename == '':
            print("No file part in the request.")
        else:
            for file in files:
                file.save(os.path.join(upload_dir, file.filename))

        # Create new workload type
        new_workload = WorkloadType(
            workload_name=workload_name,
            workload_enabled=workload_enabled,
            deploy_method=deploy_method,
            helm_repo_name=repo_name,
            helm_repo_url=repo_url,
            helm_chart=chart_name,
            helm_chart_version=chart_version,
            helm_set_values=values,
            created_by=user.username,
            created_at=datetime.now(),
        )

        db.session.add(new_workload)
        db.session.commit()
        logging.info(f"Action:Add Workload:{workload_name} Result:Success")
        return jsonify({"status": "success", "message": "Workload type added successfully."})

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding workload type: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def deploy_helm_workload(workload_id, workload, username, namespace, redeployment=False, previous_workload_id=None):
    workload_name = workload['type'].lower()
    repo_name = workload['repo_name']
    repo_url = workload['repo_url']
    chart_name = workload['chart_name']
    chart_version = workload['chart_version']
    values = workload['set_values']

    try:
        subprocess.run(['helm', 'repo', 'add', repo_name, repo_url], check=True)

        update_helm_repos()

        # Build base command
        cmd = ['helm', '-n', namespace, 'upgrade', '--install', workload_name, '--kubeconfig',
               f"{Config.KUBECONFIG_PATH}", f"{repo_name}/{chart_name}", '--post-renderer',
               './app/inject_labels_helm.py']

        # Add a version if specified
        if chart_version and chart_version != 'null':
            cmd += ['--version', chart_version]

        # Process set values
        if values and values != 'null':
            for pair in values.split(';'):
                cmd += ['--set', pair.strip()]

        # Add a values configuration file if exists
        if redeployment:
            values_file_path = os.path.join(Config.UPLOAD_FOLDER, username, str(previous_workload_id), 'values.yaml')
        else:
            values_file_path = os.path.join(Config.UPLOAD_FOLDER, str(workload_name), 'values.yaml')

        if os.path.exists(values_file_path):
            cmd += ['-f', values_file_path]

        # Set env variable for the script
        env = os.environ.copy()
        env["WORKLOAD_ID"] = str(workload_id)

        result = subprocess.run(
            cmd,
            check=True,
            # shell=True,
            capture_output=True,
            env=env
            # text=True,
            # stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
            # timeout=300
        )

        return jsonify({
            "status": "success",
            "message": "Helm deployment successful",
            # "output": result.stdout
        }), 200

    except Exception as e:
        logging.error(f"Error deploying Helm workload: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def update_helm_repos():
    """Periodically refresh Helm repositories"""
    subprocess.run(['helm', 'repo', 'update'], check=False)
