import logging
import threading

import kubernetes
from app.helm_utils import handle_helm_deployment
from app.kubernetes_utils import load_kube_config, handle_workloads, ensure_user_namespace, delete_resources
from app.models import DeployedWorkload, WorkloadType
from app.yaml_utils import handle_yaml_deployment
from flask import Blueprint, jsonify, render_template, request, url_for
from flask_login import login_required, current_user
from werkzeug.utils import redirect
from sqlalchemy import or_

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

        threading.Thread(target=handle_workloads,
                         args=(workloads, chained, current_user.username, request.form.get('namespace'))).start()

        return jsonify({"status": "success", "message": "Workload(s) submitted successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@workload_bp.route('/workload_types', methods=['GET'])
@login_required
def get_workload_types():
    if current_user.role == 'admin':
        query = WorkloadType.query.filter_by(workload_enabled=True)
    else:
        query = WorkloadType.query.filter(
            WorkloadType.workload_enabled == True,
            or_(
                WorkloadType.created_by == current_user.username,
                WorkloadType.created_by == 'admin'
            )
        )

    types = query.all()

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
        deploy_method = request.form.get('deployMethod')

        if deploy_method == 'helm':
            return handle_helm_deployment(request, current_user)
        else:
            #  logging.info("Received form data:")
            #  for key, value in request.form.items():
            #    logging.info(f"{key}: {value}")
            return handle_yaml_deployment(request, current_user)
    except Exception as e:
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


@workload_bp.route('/running_workloads', methods=['GET'])
@login_required
def running_workloads():
    if not current_user.is_authenticated:
        logging.warning('User is not authenticated.')
        return redirect(url_for('login'))

    try:
        if current_user.role == 'admin':
            workloads = DeployedWorkload.query.all()
        else:
            workloads = DeployedWorkload.query.filter(
                DeployedWorkload.username == current_user.username,
                DeployedWorkload.completed.is_(False)
            ).all()

        workload_data = []
        for workload in workloads:
            workload_data.append({
                'workload_name': workload.workload_name,
                'duration': workload.duration,
                'replicas': workload.replicas,
                'node_name': workload.node_name,
                'status': workload.status,
                'completed': workload.completed,
                'username': workload.user.username,
                'created_at': workload.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return workload_data
    except Exception as e:
        logging.error(f"Error fetching workloads: {str(e)}")
        return jsonify({'error': 'Failed to fetch workloads for user ' + current_user.username}), 500


@workload_bp.route('/delete_running_workloads', methods=['POST'])
@login_required
def delete_running_workloads():
    if not current_user.is_authenticated:
        logging.warning('User is not authenticated.')
        return redirect(url_for('login'))

    try:
        workload = request.get_json()

        if not workload:
            return jsonify({"error": "No JSON received"}), 400  # Bad Request

        delete_resources(workload, current_user.namespace)

        logging.info(f"Workload deleted successfully for user '{current_user.username}'.")
        return jsonify({"status": "success", "message": "Backend workload deleted successfully."})
    except Exception as e:
        logging.error(f"Error deleting workload: {str(e)}")
        return jsonify({'error': 'Failed to delete workload for user ' + current_user.username}), 500
