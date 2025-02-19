import logging
import os
import subprocess
import threading
import time
from datetime import datetime

import kubernetes
import yaml
from flask import jsonify
from kubernetes import utils
from kubernetes.client.rest import ApiException
from config import Config
from app import create_app, db

from app.models import DeployedWorkload, User, WorkloadType, HelmDeployment
from werkzeug.utils import secure_filename


def handle_helm_deployment(request, user):
    # Basic validation
    chart = request.form.get('helm_chart')
    release = request.form.get('helm_release')

    if not chart or not release:
        return jsonify({"status": "error", "message": "Missing required Helm parameters"}), 400

    # Build base command
    cmd = ['helm', 'install', release, chart]

    # Add version if specified
    if version := request.form.get('helm_version'):
        cmd += ['--version', version]

    # Handle repository for non-local charts
    if request.form.get('helm_repo_type') != 'local':
        repo_url = request.form.get('helm_repo_url')
        if not repo_url:
            return jsonify({"status": "error", "message": "Repository URL required"}), 400
        cmd += ['--repo', repo_url]

    # Process values files
    for values_file in request.files.getlist('helm_values'):
        if values_file and values_file.filename.endswith(('.yaml', '.yml')):
            path = os.path.join(Config.UPLOAD_FOLDER, secure_filename(values_file.filename))
            values_file.save(path)
            cmd += ['-f', path]

    # Process set values
    if set_values := request.form.get('helm_set'):
        for pair in set_values.split('\n'):
            cmd += ['--set', pair.strip()]

    # Add user-level restrictions
    if user.expertise_level == 'beginner':
        cmd = restrict_helm_command(cmd, user.level)

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        return jsonify({
            "status": "success",
            "message": "Helm deployment successful",
            "output": result.stdout
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "message": "Helm deployment failed",
            "error": e.stderr
        }), 500


def restrict_helm_command(cmd, user_level):
    """Remove dangerous flags for non-admin users"""
    allowed_flags = {
        'beginner': ['--version', '-f', '--set'],
        'intermediate': ['--version', '-f', '--set', '--atomic'],
        'advanced': None  # All flags allowed
    }

    if user_level not in allowed_flags or allowed_flags[user_level] is None:
        return cmd

    safe_cmd = []
    skip_next = False
    for i, part in enumerate(cmd):
        if skip_next:
            skip_next = False
            continue
        if part.startswith('--') and part.split('=')[0] not in allowed_flags[user_level]:
            continue
        safe_cmd.append(part)

    return safe_cmd
