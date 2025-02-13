import json

import os
import subprocess
import threading
import time
from datetime import datetime

import yaml
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from kubernetes.client.rest import ApiException
from requests import session
from werkzeug.security import generate_password_hash, check_password_hash

import kubernetes
from kubernetes import utils

app.config['SECRET_KEY'] = 'admin_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'










