import json

import requests
import logging
import base64
from flask import jsonify


def _create_auth_header(user, password):
    credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }


class GrafanaManager:
    def __init__(self, base_url, admin_user, admin_password, verify_ssl=False):
        self.base_url = base_url
        self.base_url = base_url.rstrip("/")
        self.auth_header = _create_auth_header(admin_user, admin_password)
        self.verify_ssl = verify_ssl

    def create_grafana_user(self, username, role="Viewer"):
        """Create user in Grafana if not exists"""
        if not self.user_exists(username):
            payload = {
                "name": username,
                "email": f"{username}@yourdomain.com",
                "login": username,
                "password": f"{username}",
                "OrgId": 1
            }
            response = requests.post(
                f"{self.base_url}/api/admin/users",
                json=payload,
                headers=self.auth_header,
                verify=self.verify_ssl
            )
            if response.status_code == 200:
                logging.info(f"Created Grafana user: {username}")
                self.set_user_role(response.json()['id'], role)
            return response.json()
        return None

    def create_service_account(self, username):
        payload = {
            "name": f"{username}-service-account",
            "role": "Viewer"
        }

        response = requests.post(f"{self.base_url}/api/serviceaccounts", json=payload, headers=self.auth_header)

        if response.status_code in (200, 201):
            account_id = response.json()["id"]
            logging.info("Grafana service account created.")
            payload = {
                "name": f"{username}-token",
                "role": "Viewer"
            }

            token_response = requests.post(f"{self.base_url}/api/serviceaccounts/{account_id}/tokens", json=payload,
                                           headers=self.auth_header)

            if token_response.status_code in (200, 201):
                token_value = token_response.json()["key"]
                return account_id, token_value
            else:
                return jsonify({"error": "Failed to create API token",
                                "details": token_response.json()}), token_response.status_code
        elif response.status_code == 400:
            logging.info("Grafana Service account already exists.")
        else:
            logging.info("Grafana Service account not created.")
            return jsonify(
                {"error": "Failed to create service account", "details": response.json()}), response.status_code

    def user_exists(self, username):
        response = requests.get(
            f"{self.base_url}/api/users/lookup?login={username}",
            headers=self.auth_header
        )
        return response.status_code == 200

    def set_user_role(self, user_id, role):
        payload = {"role": role}
        requests.patch(
            f"{self.base_url}/api/org/users/{user_id}",
            json=payload,
            headers=self.auth_header
        )

    def create_metrics_dashboard(self, username, namespace):
        """Create namespace-specific dashboard"""
        with open('templates/metrics-dashboard.json') as f:
            template = json.load(f)

            dashboard = {
                "dashboard": {
                    **template,
                    "title": f"Metrics Dashboard - {username}",
                    "uid": f"metrics-{username}-uid",
                    "time": {
                        "from": "now-1h",
                        "to": "now"
                    },
                    "refresh": "5s"
                },
                "overwrite": True
            }

        response = requests.post(
            f"{self.base_url}/api/dashboards/db",
            json=dashboard,
            headers=self.auth_header
        )
        return response.json()

    def create_logs_dashboard(self, username, namespace):
        """Create namespace-specific dashboard"""
        with open('templates/logs-dashboard.json') as f:
            template = json.load(f)

            dashboard = {
                "dashboard": {
                    **template,
                    "title": f"Logs Dashboard - {username}",
                    "uid": f"logs-{username}-uid",
                    "time": {
                        "from": "now-1h",
                        "to": "now"
                    },
                    "refresh": "10s"
                },
                "overwrite": True
            }

            #final_dashboard = self.replace_namespace(dashboard, "_namespace", namespace)

        response = requests.post(
            f"{self.base_url}/api/dashboards/db",
            json=dashboard,
            headers=self.auth_header
        )
        return response.json()

    def create_cluster_dashboard(self, username, namespace):
        """Create namespace-specific dashboard"""
        with open('templates/cluster-dashboard.json') as f:
            template = json.load(f)

            dashboard = {
                "dashboard": {
                    **template,
                    "title": f"Cluster-wide Resources Dashboard - {username}",
                    "uid": f"cluster-{username}-uid",
                    "time": {
                        "from": "now-1h",
                        "to": "now"
                    },
                    "refresh": "5s"
                },
                "overwrite": True
            }

        response = requests.post(
            f"{self.base_url}/api/dashboards/db",
            json=dashboard,
            headers=self.auth_header
        )
        return response.json()
