import logging
import re

from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app import db, login_manager
from app.models import User
from app.kubernetes_utils import ensure_user_namespace
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            logging.info(f'Login successful. Username: {username}')
            login_user(user)
            return redirect(url_for('workload.index'))
        else:
            logging.warning(f'Login failed. Username: {username}')
            flash('Login failed. Check your username and password.')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
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
            namespace = f"user-{re.sub(r'[^a-z0-9-]', '', username.lower())[:45]}"
            quota_pods = request.form.get('quota_pods')
            quota_cpu = request.form.get('quota_cpu')
            quota_memory = request.form.get('quota_memory')

            new_user = User(username=username, password=hashed_password, role=role, user_level=level,
                            namespace=namespace, quota_pods=quota_pods, quota_cpu=quota_cpu, quota_memory=quota_memory)

            db.session.add(new_user)
            db.session.commit()

            ensure_user_namespace(username=username, namespace=namespace, quota_pods=quota_pods, quota_cpu=quota_cpu,
                                  quota_memory=quota_memory)

            logging.info(f'User registered: Username: {username}, Role: {role}, Expertise-level: {level}')
            return jsonify({"status": "success", "message": "New user registered successfully."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})
