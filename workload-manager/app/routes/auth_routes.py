import logging

from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app import db, login_manager
from app.models import User
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    # return db.session.get(User, int(user_id))


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
            new_user = User(username=username, password=hashed_password, role=role, user_level=level)
            db.session.add(new_user)
            db.session.commit()
            logging.info(
                f'New user registered successfully. Username: {username}, Role: {role}, Expertise-level: {level}')
            return jsonify({"status": "success", "message": "New user registered successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
