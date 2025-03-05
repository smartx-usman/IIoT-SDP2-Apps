import logging
import os

from ruamel.yaml import YAML
from app import db
from app.models import WorkloadType
from config import Config
from flask import jsonify


def handle_yaml_deployment(request, user):
    try:
        config_method = request.form.get('configMethod')
        #logging.info(f"Config method: {config_method}")

        if config_method == 'upload':
            return handle_static_yaml(request, user.username)

        elif config_method == 'dynamic':
            resource_type = request.form.get('resourceType')
            yaml_content = handle_dynamic_yaml(request.form, resource_type, user.user_level, user.namespace)
            yaml_docs = [yaml_content]

            if resource_type == 'Deployment':
                service_type = request.form.get('service_type')
                #  logging.info(f"Service type: {service_type}")

                if service_type in ['NodePort', 'ClusterIP']:
                    service_spec = generate_service_yaml(request.form, service_type, user.namespace)
                    yaml_docs.append(service_spec)

            return save_generated_yaml(request, yaml_docs, user.username, resource_type)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def handle_static_yaml(request, username):
    try:
        deploy_method = request.form.get('deployMethod')
        workload_name = request.form.get('workloadDisplayName').lower().replace(' ', '-')
        workload_enabled = request.form.get('workload_enabled', 'true').lower() == 'true'
        files = request.files.getlist('files')

        # Check if workload type already exists
        if WorkloadType.query.filter_by(workload_name=workload_name).first():
            return jsonify(status='error', message='Workload with same name already exists'), 400

        # Create directory
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, str(workload_name))
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            if file and file.filename.endswith(('.yaml', '.yml')):
                file.save(os.path.join(upload_dir, file.filename))

        save_generated_type_db(workload_name, workload_enabled, username, deploy_method)

        return jsonify({"status": "success", "message": "Workload type added successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


def handle_dynamic_yaml(form_data, resource_type, user_level, namespace='default'):
    name = form_data.get('workloadDisplayName').lower().replace(' ', '-')
    image = form_data.get('image')
    container_port = form_data.get('container_port')
    cmd_interpreter = form_data.get('cmd_interpreter')
    base_spec = {}

    # Default values configuration
    default_resources = {
        'requests': {
            'cpu': '100m',  # 0.1 CPU core
            'memory': '256Mi'  # 128 Mebibytes
        },
        'limits': {
            'cpu': '500m',  # 1 CPU core
            'memory': '1Gi'  # 1 Gibibyte
        }
    }

    # Process user inputs
    resources = {}
    user_requests = {}
    user_limits = {}

    # Handle requests
    if form_data.get('cpuRequest'):
        user_requests['cpu'] = form_data['cpuRequest']
    if form_data.get('memoryRequest'):
        user_requests['memory'] = form_data['memoryRequest']

    # Handle limits
    if form_data.get('cpuLimit'):
        user_limits['cpu'] = form_data['cpuLimit']
    if form_data.get('memoryLimit'):
        user_limits['memory'] = form_data['memoryLimit']

    # Apply defaults where needed
    final_requests = user_requests or default_resources['requests']
    final_limits = user_limits or default_resources['limits']

    # Only include fields that have values
    if final_requests:
        resources['requests'] = final_requests
    if final_limits:
        resources['limits'] = final_limits

    if resource_type == 'Pod':
        base_spec = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": name,
                         "namespace": namespace},
            "spec": {
                "containers": [
                    {
                        "name": name,
                        "image": image,
                        "ports": [{"containerPort": int(container_port)}],
                        "command": [cmd_interpreter]
                    }
                ]
            },
        }

        # --- Args Handling ---
        if 'cmd_arguments' in form_data and form_data['cmd_arguments'].strip():
            base_spec['spec']['containers'][0]['args'] = [
                arg.strip() for arg in form_data['cmd_arguments'].split() if arg.strip()
            ]

        # --- Resources ---
        if resources:
            base_spec['spec']['containers'][0]['resources'] = resources

        # Add key only if value exists
        def add_if_exists(dictionary, key, value):
            if value:
                dictionary[key] = value

        if user_level == 'intermediate' or user_level == 'advanced':
            # --- Environment Variables ---
            env_names = form_data.getlist('envName[]')
            env_values = form_data.getlist('envValue[]')

            env_vars = []
            for name, value in zip(env_names, env_values):
                if name.strip() and value.strip():
                    env_vars.append({"name": name, "value": value})

            if env_vars:
                base_spec['spec']['containers'][0]['env'] = env_vars

            # --- Volumes & VolumeMounts ---
            volumes = []
            volume_mounts = []

            # Get all volume-related data
            volume_names = form_data.getlist('volumeName[]')
            volume_types = form_data.getlist('volumeType[]')
            volume_sources = form_data.getlist('volumeSource[]')
            mount_paths = form_data.getlist('mountPath[]')

            for i in range(len(volume_names)):
                vol_name = volume_names[i]
                vol_type = volume_types[i] if i < len(volume_types) else None
                vol_source = volume_sources[i] if i < len(volume_sources) else None
                mount_path = mount_paths[i] if i < len(mount_paths) else None

                if not vol_name or not vol_type or not mount_path:
                    continue  # Skip incomplete entries

                # Build volume configuration
                volume = {"name": vol_name}
                if vol_type == "hostPath":
                    volume["hostPath"] = {"path": vol_source} if vol_source else {}
                elif vol_type == "configMap":
                    volume["configMap"] = {"name": vol_source} if vol_source else {}
                elif vol_type == "emptyDir":
                    volume["emptyDir"] = {}

                volumes.append(volume)
                volume_mounts.append({
                    "name": vol_name,
                    "mountPath": mount_path
                })

            if volumes:
                base_spec['spec']['volumes'] = volumes
                base_spec['spec']['containers'][0]['volumeMounts'] = volume_mounts

            # --- Policies ---
            add_if_exists(base_spec['spec']['containers'][0], 'imagePullPolicy', form_data.get('imagePullPolicy'))

        if user_level in ['advanced']:
            # --- Policies ---
            add_if_exists(base_spec['spec'], 'restartPolicy', form_data.get('restartPolicy'))

            # --- Security Context ---
            security_context = {}
            if form_data.get('runAsUser'):
                security_context['runAsUser'] = int(form_data['runAsUser'])
            if form_data.get('runAsGroup'):
                security_context['runAsGroup'] = int(form_data['runAsGroup'])
            if 'privileged' in form_data:
                security_context['privileged'] = bool(form_data['privileged'])
            if security_context:
                base_spec['spec']['containers'][0]['securityContext'] = security_context

            # --- Probes ---
            def build_probe(prefix):
                path = form_data.get(f'{prefix}Path')
                port = form_data.get(f'{prefix}Port')
                delay = form_data.get(f'{prefix}InitialDelay')
                if path and port and delay:
                    return {
                        "httpGet": {"path": path, "port": int(port)},
                        "initialDelaySeconds": int(delay)
                    }
                return None

            liveness_probe = build_probe('liveness')
            if liveness_probe:
                base_spec['spec']['containers'][0]['livenessProbe'] = liveness_probe

            readiness_probe = build_probe('readiness')
            if readiness_probe:
                base_spec['spec']['containers'][0]['readinessProbe'] = readiness_probe

            # --- Affinity ---
            affinity_key = form_data.get('nodeAffinityKey')
            affinity_value = form_data.get('nodeAffinityValue')
            if affinity_key and affinity_value:
                base_spec['spec']['affinity'] = {
                    "nodeAffinity": {
                        "requiredDuringSchedulingIgnoredDuringExecution": {
                            "nodeSelectorTerms": [{
                                "matchExpressions": [{
                                    "key": affinity_key,
                                    "operator": "In",
                                    "values": [affinity_value]
                                }]
                            }]
                        }
                    }
                }

            # --- Tolerations ---
            toleration_key = form_data.get('tolerationKey')
            toleration_value = form_data.get('tolerationValue')
            toleration_effect = form_data.get('tolerationEffect')
            if toleration_key and toleration_value and toleration_effect:
                base_spec['spec']['tolerations'] = [{
                    "key": toleration_key,
                    "operator": "Equal",
                    "value": toleration_value,
                    "effect": toleration_effect
                }]

    elif resource_type == 'Deployment':
        replicas = form_data.get('replicas')

        base_spec = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": name,
                         "namespace": namespace},
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
                                "command": [cmd_interpreter]
                            }
                        ]
                    }
                },
            },
        }

        # Add key only if value exists
        def add_if_exists(dictionary, key, value):
            if value:
                dictionary[key] = value

        # --- Args Handling ---
        if 'cmd_arguments' in form_data and form_data['cmd_arguments'].strip():
            base_spec['spec']['template']['spec']['containers'][0]['args'] = [
                arg.strip() for arg in form_data['cmd_arguments'].split() if arg.strip()
            ]

        # --- Resources ---
        if resources:
            base_spec['spec']['template']['spec']['containers'][0]['resources'] = resources

        if user_level == 'intermediate' or user_level == 'advanced':
            # --- Environment Variables ---
            env_names = form_data.getlist('envName[]')
            env_values = form_data.getlist('envValue[]')

            env_vars = []
            for name, value in zip(env_names, env_values):
                if name.strip() and value.strip():
                    env_vars.append({"name": name, "value": value})

            if env_vars:
                base_spec['spec']['template']['spec']['containers'][0]['env'] = env_vars

            # --- Volumes & VolumeMounts ---
            volumes = []
            volume_mounts = []

            # Get all volume-related data
            volume_names = form_data.getlist('volumeName[]')
            volume_types = form_data.getlist('volumeType[]')
            volume_sources = form_data.getlist('volumeSource[]')
            mount_paths = form_data.getlist('mountPath[]')

            for i in range(len(volume_names)):
                vol_name = volume_names[i]
                vol_type = volume_types[i] if i < len(volume_types) else None
                vol_source = volume_sources[i] if i < len(volume_sources) else None
                mount_path = mount_paths[i] if i < len(mount_paths) else None

                if not vol_name or not vol_type or not mount_path:
                    continue  # Skip incomplete entries

                # Build volume configuration
                volume = {"name": vol_name}
                if vol_type == "hostPath":
                    logging.info(f"Volume type: {vol_type}")
                    volume["hostPath"] = {"path": vol_source, "type": "Directory"} if vol_source else {}
                elif vol_type == "configMap":
                    volume["configMap"] = {"name": vol_source} if vol_source else {}
                elif vol_type == "emptyDir":
                    volume["emptyDir"] = {}

                volumes.append(volume)
                volume_mounts.append({
                    "name": vol_name,
                    "mountPath": mount_path
                })

            if volumes:
                base_spec['spec']['template']['spec']['volumes'] = volumes
                base_spec['spec']['template']['spec']['containers'][0]['volumeMounts'] = volume_mounts

            # --- Policies ---
            add_if_exists(base_spec['spec']['template']['spec']['containers'][0], 'imagePullPolicy', form_data.get('imagePullPolicy'))

        if user_level == 'advanced':
            # --- Policies ---
            add_if_exists(base_spec['spec']['template']['spec'], 'restartPolicy', form_data.get('restartPolicy'))

            # --- Security Context ---
            security_context = {}
            if form_data.get('runAsUser'):
                security_context['runAsUser'] = int(form_data['runAsUser'])
            if form_data.get('runAsGroup'):
                security_context['runAsGroup'] = int(form_data['runAsGroup'])
            if 'privileged' in form_data:
                security_context['privileged'] = bool(form_data['privileged'])
            if security_context:
                base_spec['spec']['template']['spec']['containers'][0]['securityContext'] = security_context

            # --- Probes ---
            def build_probe(prefix):
                path = form_data.get(f'{prefix}Path')
                port = form_data.get(f'{prefix}Port')
                delay = form_data.get(f'{prefix}InitialDelay')
                if path and port and delay:
                    return {
                        "httpGet": {"path": path, "port": int(port)},
                        "initialDelaySeconds": int(delay)
                    }
                return None

            liveness_probe = build_probe('liveness')
            if liveness_probe:
                base_spec['spec']['template']['spec']['containers'][0]['livenessProbe'] = liveness_probe

            readiness_probe = build_probe('readiness')
            if readiness_probe:
                base_spec['spec']['template']['spec']['containers'][0]['readinessProbe'] = readiness_probe

            # --- Affinity ---
            affinity_key = form_data.get('nodeAffinityKey')
            affinity_value = form_data.get('nodeAffinityValue')
            if affinity_key and affinity_value:
                base_spec['spec']['template']['spec']['affinity'] = {
                    "nodeAffinity": {
                        "requiredDuringSchedulingIgnoredDuringExecution": {
                            "nodeSelectorTerms": [{
                                "matchExpressions": [{
                                    "key": affinity_key,
                                    "operator": "In",
                                    "values": [affinity_value]
                                }]
                            }]
                        }
                    }
                }

            # --- Tolerations ---
            toleration_key = form_data.get('tolerationKey')
            toleration_value = form_data.get('tolerationValue')
            toleration_effect = form_data.get('tolerationEffect')
            if toleration_key and toleration_value and toleration_effect:
                base_spec['spec']['template']['spec']['tolerations'] = [{
                    "key": toleration_key,
                    "operator": "Equal",
                    "value": toleration_value,
                    "effect": toleration_effect
                }]

        logging.info(f"Generated Deployment YAML: {base_spec}")

    # elif resource_type == 'StatefulSet':
    # Add the statefulset spec here
    # elif resource_type == 'DaemonSet':
    # Add the daemonset spec here
    # elif resource_type == 'Job':
    # Add the job spec here

    return base_spec


def generate_service_yaml(form_data, service_type, namespace='default'):
    name = form_data.get('workloadDisplayName').lower().replace(' ', '-')
    service_spec = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{name}-service",
            "namespace": namespace
        },
        "spec": {
            "type": service_type,
            "selector": {"app": name},  # Must match Deployment's pod labels
            "ports": [{
                "protocol": form_data.get('svcProtocol'),
                "port": int(form_data['svcPort']),
                "targetPort": int(form_data['targetPort'])
            }]
        }
    }

    if service_type == 'NodePort':
        service_spec['spec']['ports'][0]['nodePort'] = int(form_data['nodePort'])

    return service_spec


def save_generated_yaml(request, data, username, resource_type):
    try:
        deploy_method = request.form.get('deployMethod')
        workload_name = request.form.get('workloadDisplayName').lower().replace(' ', '-')
        workload_enabled = request.form.get('workload_enabled', 'true').lower() == 'true'

        # Check if workload type already exists
        if WorkloadType.query.filter_by(workload_name=workload_name).first():
            return jsonify(status='error', message='Workload with same name already exists'), 400

        # Create directory using ID
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, str(workload_name))
        os.makedirs(upload_dir, exist_ok=True)

        yaml = YAML()
        yaml.indent(sequence=4, offset=2)
        yaml.preserve_quotes = True

        with open(os.path.join(upload_dir, f"{resource_type.lower()}.yaml"), "w") as file_handler:
            yaml.dump_all(data, file_handler)

        save_generated_type_db(workload_name, workload_enabled, username, deploy_method)

        logging.info(f"Workload type added successfully: {workload_name}")
        return jsonify({"status": "success", "message": f"Workload type {workload_name} added successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


def save_generated_type_db(workload_name, workload_enabled, username, deploy_method):
    # Create new workload type
    new_workload = WorkloadType(
        workload_name=workload_name,
        workload_enabled=workload_enabled,
        deploy_method=deploy_method,
        created_by=username
    )

    db.session.add(new_workload)
    db.session.commit()
