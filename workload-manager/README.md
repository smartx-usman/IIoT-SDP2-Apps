# Workload Manager
We will deploy workload manager to the master node of a Kubernetes cluster along with an NGINX Ingress controller to manage external access using HTTPS. The deployment also includes an observability stack with Prometheus, Grafana, Loki, and Telegraf for monitoring and logging.

## How to deploy

```shell
# Set master node IP and let others to default values
MASTER_IP="192.168.60.146"
DNS_NAME="master.local"
NAMESPACE="simulation"
PROMETHEUS_URL="http://prometheus-server.${NAMESPACE}.svc.cluster.local"
LOKI_URL="http://loki-headless.${NAMESPACE}.svc.cluster.local:3100"
GRAFANA_INTERNAL_URL="http://grafana-exp.${NAMESPACE}.svc.cluster.local:3000"
GRAFANA_PUBLIC_URL="https://${DNS_NAME}:30009" #https://master.local:30009

# Create namespace
kubectl create namespace "${NAMESPACE}"

# Make sure record exists in /etc/hosts on master and local system from where you access workload-manager in the Browser
if ! grep -q "\s$DNS_NAME" /etc/hosts; then
    echo "$MASTER_IP $DNS_NAME" | sudo tee -a /etc/hosts
fi

# Update configs in openssl-san.conf
sed -i "s/IP_ADDRESS/${MASTER_IP}/g" openssl-san.conf
sed -i "s/DNS_NAME/${DNS_NAME}/g" openssl-san.conf

# Deploy nginx ingress controller
kubectl apply -f ingress-nginx.yaml

# Create certificates and keys for https
mkdir certs
cd certs
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout certs/tls.key -out certs/tls.crt \
  -config openssl-san.conf -extensions req_ext

# Create a secret for cert and key
kubectl create secret -n ${NAMESPACE} tls workload-manager-tls \
  --cert=certs/tls.crt \
  --key=certs/tls.key

# Update Grafana datasources configurations
sed -i "s|PROMETHEUS_URL|${PROMETHEUS_URL}|g" monitoring/grafana-values.yaml
sed -i "s|LOKI_URL|${LOKI_URL}|g" monitoring/grafana-values.yaml

# Install Observability Stack (If not installed then workload manager deployment will fail)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm upgrade --install prometheus prometheus-community/prometheus -f monitoring/prometheus-values.yaml -n ${NAMESPACE}
helm upgrade --install loki grafana/loki -f monitoring/loki-values.yaml -n ${NAMESPACE}
helm upgrade --install grafana-exp grafana/grafana -f monitoring/grafana-values.yaml -n ${NAMESPACE}
sleep 60
kubectl apply -f monitoring/telegraf-serviceaccount.yaml -n ${NAMESPACE}
kubectl apply -f monitoring/telegraf.yaml -n ${NAMESPACE}

# Update config, Create ClusterIP service and Deploy workload manager
sed -i "s|GRAFANA_INT_URL|${GRAFANA_INTERNAL_URL}|g" workload-manager-deployment.yaml
sed -i "s|GRAFANA_PUB_URL|${GRAFANA_PUBLIC_URL}|g" workload-manager-deployment.yaml
kubectl apply -f workload-manager-deployment.yaml

# Create Ingress
kubectl apply -f ingress.yaml
```

## Accessing Workload Manager
Open your browser and navigate to https://master.local:30009/workload-manager (or the DNS name you have set). You should see the Workload Manager interface.