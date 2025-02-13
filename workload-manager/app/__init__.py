from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

import logging

db = SQLAlchemy()
login_manager = LoginManager()

# Suppress Flask's default logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    # login_manager.login_view = 'login'

    from app.routes.auth_routes import auth_bp
    from app.routes.workload_routes import workload_bp
    from app.routes.monitoring_routes import monitoring_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(workload_bp)
    app.register_blueprint(monitoring_bp)

    with app.app_context():
        db.create_all()
        from app.utilities import create_default_admin, initialize_default_workloads
        create_default_admin()
        initialize_default_workloads()

    return app
