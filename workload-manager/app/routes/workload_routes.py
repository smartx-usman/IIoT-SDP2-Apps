import logging
import os
import threading
import time

import kubernetes
from app.helm_utils import add_helm_type_workload
from app.kubernetes_utils import load_kube_config, handle_workloads, ensure_user_namespace, delete_resources
from app.models import DeployedWorkload, WorkloadType
from app.yaml_utils import add_yaml_type_workload
from flask import Blueprint, jsonify, render_template, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from config import Config

workload_bp = Blueprint('workload', __name__)


@workload_bp.route('/workload-manager')
@login_required
def index():
    grafana_internal_url = f"{Config.GRAFANA_INTERNAL_URL}"
    grafana_public_url = f"{Config.GRAFANA_PUBLIC_URL}"
    return render_template('index.html', grafana_internal_url=grafana_internal_url, grafana_public_url=grafana_public_url)


@workload_bp.route('/workload-manager/nodes', methods=['GET'])
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


@workload_bp.route('/workload-manager/deployed_workloads', methods=['GET'])
@login_required
def deployed_workloads():
    try:
        if current_user.role == 'admin':
            # workloads = DeployedWorkload.query.all()
            workloads = DeployedWorkload.query.options(
                joinedload(DeployedWorkload.yaml_workload),
                joinedload(DeployedWorkload.helm_workload)
            ).all()
        else:
            # workloads = DeployedWorkload.query.filter_by(username=current_user.username).all()
            workloads = DeployedWorkload.query.filter_by(username=current_user.username).options(
                joinedload(DeployedWorkload.yaml_workload),
                joinedload(DeployedWorkload.helm_workload),
                # joinedload(DeployedWorkload.workload_type)
            ).all()

        workload_data = []
        for workload in workloads:
            workload_info = {
                'workload_id': workload.workload_id,
                'workload_name': workload.workload_name,
                'duration': workload.duration,
                'deploy_method': workload.workload_type.deploy_method,
                'status': workload.deployment_status,
                'is_completed': workload.is_completed,
                'username': workload.user.username,
                'created_at': workload.created_at.isoformat(),
                'finished_at': workload.finished_at.isoformat(),
                # .strftime('%Y-%m-%d %H:%M:%S')
            }

            if workload.yaml_workload:
                workload_info.update({
                    'replicas': workload.yaml_workload.replicas,
                    'node_name': workload.yaml_workload.node_name,
                })
            elif workload.helm_workload:
                # helm_set_values = {}
                # if workload.helm_workload.set_values:
                #    helm_set_values = workload.helm_workload.set_values
                workload_info.update({
                    'chart_name': workload.helm_workload.chart_name,
                    'chart_version': workload.helm_workload.chart_version,
                    'set_values': workload.helm_workload.set_values,
                })
            else:
                continue

            workload_data.append(workload_info)

        return workload_data
    except Exception as e:
        logging.error(f"Action:Fetch Result:Error Trace:{str(e)}")
        return jsonify({'error': 'Failed to fetch workloads for user ' + current_user.username}), 500


@workload_bp.route("/workload-manager/list_files", methods=["GET"])
@login_required
def list_files():
    folder = request.args.get("folder")
    base_path = os.path.join(Config.UPLOAD_FOLDER, folder)

    if not os.path.isdir(base_path):
        return jsonify([])

    yaml_files = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith((".yaml", ".yml")):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, base_path)
                yaml_files.append(relative_path)

    if not yaml_files:
        return "Folder is empty", 404

    return jsonify(yaml_files)


@workload_bp.route("/workload-manager/get_yaml", methods=["GET"])
@login_required
def get_yaml():
    folder = request.args.get("folder")
    filename = request.args.get("filename")
    path = os.path.join(Config.UPLOAD_FOLDER, folder, filename)

    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return "File not found", 404


@workload_bp.route("/workload-manager/save_yaml", methods=["POST"])
@login_required
def save_yaml():
    try:
        data = request.get_json()
        folder = data["folder"]
        filename = data["filename"]
        content = data["content"]
        path = os.path.join(Config.UPLOAD_FOLDER, folder, filename)

        # Optionally validate path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"{filename} saved successfully!"
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@workload_bp.route('/workload-manager/deploy_workload', methods=['POST'])
@login_required
def deploy_workload():
    try:
        workloads = []
        deploy_method = request.form.getlist('deploy_method[]')
        workload_types = request.form.getlist('workload_type[]')
        durations = request.form.getlist('duration[]')
        durations = [int(duration) for duration in durations]
        replicas = [int(r) for r in request.form.getlist('replicas[]') if r.isdigit()]
        node_names = request.form.getlist('node_name[]')

        helm_repo_names = request.form.getlist('helm_repo_name[]') if 'helm_repo_name[]' in request.form else []
        helm_repos_urls = request.form.getlist('helm_repo_url[]') if 'helm_repo_url[]' in request.form else []
        helm_charts = request.form.getlist('helm_chart[]') if 'helm_chart[]' in request.form else []
        helm_chart_versions = request.form.getlist(
            'helm_chart_version[]') if 'helm_chart_version[]' in request.form else []
        helm_values = request.form.getlist('helm_set_values[]') if 'helm_set_values[]' in request.form else []

        for i in range(len(workload_types)):
            workload = {
                'deploy_method': deploy_method[i],
                'type': workload_types[i],
                'duration': durations[i],
            }

            if deploy_method[i] == 'yaml':
                workload.update({
                    'replicas': replicas[i],
                    'node_name': node_names[i],
                })
            else:
                workload.update({
                    'repo_name': helm_repo_names[i] if i < len(helm_repo_names) else None,
                    'repo_url': helm_repos_urls[i] if i < len(helm_repos_urls) else None,
                    'chart_name': helm_charts[i] if i < len(helm_charts) else None,
                    'chart_version': helm_chart_versions[i] if i < len(helm_chart_versions) else None,
                    'set_values': helm_values[i] if i < len(helm_values) else None,
                })

            workloads.append(workload)

        start = time.time()
        threading.Thread(target=handle_workloads,
                         args=(workloads, current_user.username, request.form.get('namespace'))).start()

        logging.info(f"Action:Measurement Function:handle_workloads Delay:{(time.time() - start) * 1000} ms")

        return jsonify({"status": "success", "message": "Workload(s) submitted successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@workload_bp.route('/workload-manager/redeploy_workload', methods=['POST'])
@login_required
def redeploy_workload():
    try:
        workloads = []
        redeployment = True
        previous_workload_id = request.get_json().get('workload_id')
        #logging.info(f'Redeploying workload from Previous workload with ID: {previous_workload_id}')

        result = DeployedWorkload.query.options(
            joinedload(DeployedWorkload.yaml_workload),
            joinedload(DeployedWorkload.helm_workload)
        ).filter(DeployedWorkload.workload_id == previous_workload_id).all()

        if not result:
            return jsonify({"error": "Workload not found"}), 404

        for row in result:
            workload = {
                'deploy_method': row.workload_type.deploy_method,
                'type': row.workload_type.workload_name,
                'duration': row.duration,
            }

            if row.workload_type.deploy_method == 'yaml':
                workload.update({
                    'replicas': row.yaml_workload.replicas,
                    'node_name': row.yaml_workload.node_name,
                })
            else:
                workload.update({
                    'repo_name': row.workload_type.helm_repo_name,
                    'repo_url': row.workload_type.helm_repo_url,
                    'chart_name': row.workload_type.helm_chart,
                    'chart_version': row.workload_type.helm_chart_version,
                    'set_values': row.workload_type.helm_set_values,
                })

            #logging.info(f"Redeploying)   workload: {workload}")

            workloads.append(workload)

        threading.Thread(target=handle_workloads,
                         args=(workloads, current_user.username, current_user.namespace, redeployment,
                               previous_workload_id, result)).start()

        return jsonify({"status": "success", "message": "Workload(s) submitted successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@workload_bp.route('/workload-manager/edit_and_redeploy/<int:previous_workload_id>', methods=['POST'])
@login_required
def edit_and_redeploy(previous_workload_id):
    try:
        workloads = []
        redeployment = True
        #original = DeployedWorkload.query.get_or_404(previous_workload_id)

        result = DeployedWorkload.query.options(
            joinedload(DeployedWorkload.yaml_workload),
            joinedload(DeployedWorkload.helm_workload)
        ).filter(DeployedWorkload.workload_id == previous_workload_id).all()

        #logging.info(f"Editing and redeploying workload with ID: {previous_workload_id}")
        data = request.get_json()
        method = data.get('method')
        #logging.info(f'Received data for redeployment: {data}')

        workload = {
            'duration': data.get('duration'),
            'deploy_method': method,
            'type': data.get('workload_name'),
        }

        if method == 'yaml':
            workload.update({
                'replicas': data.get('replicas'),
                'node_name': data.get('node_name'),
            })
        elif method == 'helm':
            for row in result:
                workload.update({
                    'repo_name': row.workload_type.helm_repo_name,
                    'repo_url': row.workload_type.helm_repo_url,
                    'chart_name': data.get('chart_name'),
                    'chart_version': data.get('version'),
                    'set_values': data.get('values'),
                })

        workloads.append(workload)

        threading.Thread(target=handle_workloads,
                         args=(workloads, current_user.username, current_user.namespace, redeployment,
                               previous_workload_id, result)).start()

        return jsonify({"status": "success", "message": "Workload(s) redeployment request submitted successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@workload_bp.route('/workload-manager/workload_templates', methods=['GET'])
@login_required
def get_workload_templates():
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
            "workload_name": wt.workload_name,
            "deploy_method": wt.deploy_method,
            "helm_repo_name": wt.helm_repo_name,
            "helm_repo_url": wt.helm_repo_url,
            "helm_chart": wt.helm_chart,
            "helm_chart_version": wt.helm_chart_version,
            "helm_set_values": wt.helm_set_values,
        } for wt in types]
    })


@workload_bp.route('/workload-manager/create_workload_template', methods=['POST'])
@login_required
def create_workload_template():
    try:
        deploy_method = request.form.get('deployMethod')

        if deploy_method == 'helm':
            return add_helm_type_workload(request, current_user)
        else:
            #  logging.info("Received form data:")
            #  for key, value in request.form.items():
            #    logging.info(f"{key}: {value}")
            return add_yaml_type_workload(request, current_user)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@workload_bp.route('/workload-manager/running_workloads', methods=['GET'])
@login_required
def running_workloads():
    try:
        if current_user.role == 'admin':
            query = DeployedWorkload.query.options(
                joinedload(DeployedWorkload.workload_type),
                joinedload(DeployedWorkload.yaml_workload),
                joinedload(DeployedWorkload.helm_workload)
            ).filter(DeployedWorkload.is_completed.is_(False))

        else:
            query = DeployedWorkload.query.options(
                joinedload(DeployedWorkload.workload_type),
                joinedload(DeployedWorkload.yaml_workload),
                joinedload(DeployedWorkload.helm_workload)
            ).filter(
                DeployedWorkload.username == current_user.username,
                DeployedWorkload.is_completed.is_(False)
            )

        workloads = query.all()

        workload_data = []
        for workload in workloads:
            workload_data.append({
                'workload_id': workload.workload_id,
                'deploy_method': workload.workload_type.deploy_method,
                'workload_name': workload.workload_name,
                'duration': workload.duration,
                'completed': workload.is_completed,
                'username': workload.user.username,
                'created_at': workload.created_at.isoformat()
            })

        return workload_data
    except Exception as e:
        logging.error(f"Error fetching workloads: {str(e)}")
        return jsonify({'error': 'Failed to fetch workloads for user ' + current_user.username}), 500


@workload_bp.route('/workload-manager/delete_running_workloads', methods=['POST'])
@login_required
def delete_running_workloads():
    try:
        workload = request.get_json()

        if not workload:
            return jsonify({"error": "No JSON received"}), 400  # Bad Request

        delete_resources(workload, current_user.namespace, current_user.username)

        logging.info(
            f"Action:Delete Workload: {workload.get('workload_name')} Namespace:{current_user.namespace} User:{current_user.username} Result:Success")
        return jsonify({"status": "success", "message": "Backend workload deleted successfully."})
    except Exception as e:
        logging.error(f"Action:Delete Namespace:{current_user.namespace} Result:Error Trace:{str(e)}")
        return jsonify({'error': 'Failed to delete workload for user ' + current_user.username}), 500
