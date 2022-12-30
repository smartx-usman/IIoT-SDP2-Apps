# Install ThingsBoard in a Kubernetes Cluster

### Prerequisites
- Kubernetes 1.12+
- Helm 3.0+

### Install ThingsBoard Using Helm
```shell
helm upgrade --create-namespace -n thingsboard --install thingsboard thingsboard/thingsboard -f helm/thingsboard.yaml --set http.replicaCount=0 --set coap.replicaCount=0
```

### Install ThingsBoard Using Scripts
Create required directories on the worker node where you intend to deploy pods and create persistent volumes.
```shell
sudo mkdir /opt/persistent-volumes/
sudo mkdir /opt/persistent-volumes/pg /opt/persistent-volumes/zk /opt/persistent-volumes/kafka /opt/persistent-volumes/tb /opt/persistent-volumes/http /opt/persistent-volumes/coap /opt/persistent-volumes/mqtt
kubectl apply -f k8s/volume.yaml
```

Install ingress controller if not installed in Kubernetes cluster. Before installation, set service.externalIPs to the public IP of master node.
```shell
helm upgrade --install ingress-nginx ingress-nginx --repo https://kubernetes.github.io/ingress-nginx --namespace ingress-nginx --create-namespace -f k8s/ingress-controller.yaml
```

Install ThingsBoard using following commands (make changes to control the number of replicas and other configs).
```shell
./k8s/minikube/k8s-install-tb.sh --loadDemo
./k8s/minikube/k8s-deploy-thirdparty.sh
./k8s/minikube/k8s-deploy-resources.sh
```

Once installed, use following credentials to login to the ThingsBoard:
- System Administrator: sysadmin@thingsboard.org / sysadmin
- Tenant Administrator: tenant@thingsboard.org / tenant
- Customer User: customer@thingsboard.org / customer