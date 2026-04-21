import logging
import re

import requests
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from app import db, login_manager
from app.models import User
from app.kubernetes_utils import ensure_user_namespace
from app.grafana_manager import GrafanaManager
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config

auth_bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route('/workload-manager/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            logging.info(f'Login successful. Username: {username}')
            login_user(user)

            # Create a session for Grafana
            payload = {
                "user": username,
                "password": password
            }
            grafana_session = requests.Session()

            response = grafana_session.post(f"{Config.GRAFANA_INTERNAL_URL}/login", json=payload)

            # Store session in user context
            session["grafana_cookies"] = response.cookies.get_dict()
            current_user.grafana_session = grafana_session

            return redirect(url_for('workload.index'))
        else:
            logging.warning(f'Login failed. Username: {username}')
            flash('Login failed. Check your username and password.')
    return render_template('login.html')


@auth_bp.route('/workload-manager/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/workload-manager/register', methods=['GET', 'POST'])
def register():
    try:
        if current_user.role != 'admin':
            return redirect(url_for('workload.index'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            level = request.form.get('level')
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            namespace = f"{re.sub(r'[^a-z0-9-]', '', username.lower())[:45]}"
            quota_pods = request.form.get('quota_pods')
            quota_cpu = request.form.get('quota_cpu')
            quota_memory = request.form.get('quota_memory')

            new_user = User(username=username, password=hashed_password, role=role, user_level=level,
                            namespace=namespace, quota_pods=quota_pods, quota_cpu=quota_cpu, quota_memory=quota_memory)

            ensure_user_namespace(username=username, namespace=namespace, quota_pods=quota_pods, quota_cpu=quota_cpu,
                                  quota_memory=quota_memory)

            grafana_mgr = GrafanaManager(
                Config.GRAFANA_INTERNAL_URL,
                Config.GRAFANA_ADMIN_USER,
                Config.GRAFANA_ADMIN_PASSWORD,
                verify_ssl=False
            )
            if not grafana_mgr.user_exists(username):
                grafana_mgr.create_grafana_user(username=username)
                grafana_mgr.create_cluster_dashboard(username, namespace)
                grafana_mgr.create_metrics_dashboard(username, namespace)
                grafana_mgr.create_logs_dashboard(username, namespace)

            db.session.add(new_user)
            db.session.commit()

            logging.info(f'User registered: Username: {username}, Role: {role}, Expertise-level: {level}')
            return jsonify({"status": "success", "message": "New user registered successfully."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})


@auth_bp.route('/workload-manager/get_user/<username>', methods=['GET'])
@login_required
def get_user(username):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'username': user.username,
        'role': user.role,
        'user_level': user.user_level,
        'quota_pods': user.quota_pods,
        'quota_cpu': user.quota_cpu,
        'quota_memory': user.quota_memory
    })


@auth_bp.route('/workload-manager/update_user', methods=['POST'])
@login_required
def update_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()

    if user:
        user.role = request.form.get('role')
        user.user_level = request.form.get('level')
        user.quota_pods = request.form.get('quota_pods')
        user.quota_cpu = request.form.get('quota_cpu')
        user.quota_memory = request.form.get('quota_memory')

        # Only update password if a new one is provided
        new_password = request.form.get('password')
        if new_password:
            user.password = generate_password_hash(new_password)

        db.session.commit()
        logging.info(f'User details updated: Username: {username}')
        return jsonify({"status": "success", "message": 'User details updated successfully!'})

    return jsonify({'error': 'Update failed'}), 400