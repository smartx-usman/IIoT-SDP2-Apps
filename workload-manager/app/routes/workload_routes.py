import logging
import os

from flask import Blueprint, jsonify, render_template, request, url_for
from flask_login import login_user, login_required, logout_user, current_user
from app import db
from app.models import DeployedWorkload, User, WorkloadType
from app.kubernetes_utils import load_kube_config, handle_workloads
import kubernetes
import threading
from config import Config

from werkzeug.utils import redirect

workload_bp = Blueprint('workload', __name__)


@workload_bp.route('/')
@login_required
def index():
    return render_template('index.html')


@workload_bp.route('/nodes', methods=['GET'])
@login_required
def get_nodes():
    load_kube_config()
    v1 = kubernetes.client.CoreV1Api()
    ret = v1.list_node()
    nodes = []
    for i in ret.items:
        for condition in i.status.conditions:
            if condition.type == 'Ready' and condition.status == 'True' and "node-role.kubernetes.io/control-plane" not in i.metadata.labels:
                for address in i.status.addresses:
                    if address.type == 'Hostname':
                        nodes.append(address.address)
    return jsonify({"nodes": nodes})


@workload_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    try:
        workloads = []
        chained = False
        workload_types = request.form.getlist('workload_type[]')
        durations = request.form.getlist('duration[]')
        durations = [int(duration) for duration in durations]
        replicas = request.form.getlist('replicas[]')
        node_names = request.form.getlist('node_name[]')

        for i in range(len(workload_types)):
            workloads.append({
                'type': workload_types[i],
                'duration': int(durations[i]),
                'replicas': int(replicas[i]),
                'node_name': node_names[i]
            })

        threading.Thread(target=handle_workloads, args=(workloads, chained, current_user.username)).start()

        return jsonify({"status": "success", "message": "Workload submitted successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@workload_bp.route('/workload_types', methods=['GET'])
@login_required
def get_workload_types():
    types = WorkloadType.query.filter_by(workload_enabled=True).all()
    return jsonify({
        "types": [{
            "id": wt.id,
            "workload_name": wt.workload_name
        } for wt in types]
    })


@workload_bp.route('/add_workload_type', methods=['POST'])
@login_required
def add_workload_type():
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
        #if not os.path.exists(f'{Config.UPLOAD_FOLDER / workload_key}'):
        #    os.makedirs(f'{Config.UPLOAD_FOLDER / workload_key}')

        for file in files:
            if file and file.filename.endswith(('.yaml', '.yml')):
                file.save(os.path.join(upload_dir, file.filename))
                #file_path = os.path.join(
                #    f'{Config.UPLOAD_FOLDER / workload_key}',
                #    file.filename
                #)
                #file.save(file_path)

        return jsonify({"status": "success", "message": "Workload type added successfully."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@workload_bp.route('/deployed_workloads', methods=['GET'])
@login_required
def deployed_workloads():
    if not current_user.is_authenticated:
        logging.warning('User is not authenticated.')
        return redirect(url_for('login'))

    try:
        if current_user.role == 'admin':
            workloads = DeployedWorkload.query.all()
        else:
            workloads = DeployedWorkload.query.filter_by(username=current_user.username).all()

        logging.info(f"Workloads fetched successfully for user '{current_user.username}'.")

        workload_data = []
        for workload in workloads:
            workload_data.append({
                'workload_name': workload.workload_name,
                'duration': workload.duration,
                'replicas': workload.replicas,
                'node_name': workload.node_name,
                'status': workload.status,
                'username': workload.user.username,
                'created_at': workload.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return workload_data
    except Exception as e:
        logging.error(f"Error fetching workloads: {str(e)}")
        return jsonify({'error': 'Failed to fetch workloads for user ' + current_user.username}), 500
