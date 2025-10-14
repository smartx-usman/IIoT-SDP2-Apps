# File Server
This is a simple file server that serves files from a specified directory over HTTP. It uses Python's built-in http.server module to handle incoming requests.

## Usage
To run the file server locally, you can use the following command:
```shell
python3 file-server.py
```

This will start the file server and serve files from the current directory at http://localhost:8000/.

To run the file server in a Docker container, you can build the Docker image with the following command:
```shell    
docker build -t file-server .
```

Then, you can run the Docker container with the following command:
```shell
docker run -p 8000:8000 file-server
```
This will start the container and map port 8000 in the container to port 8000 on the host machine. You can then access the file server at http://localhost:8000/.

## Deployment in Kubernetes
To deploy the file server in Kubernetes, you can use the included file-server.yaml file. This file defines a Deployment with three replicas and a PersistentVolumeClaim named file-server-pvc. The file server serves files from the /files directory, which is mounted as a volume in the container.

To deploy the file server, run the following command:
```shell
kubectl apply -f file-server/file-server.yaml
```

This will create the Deployment and a NodePort Service that exposes the file server on port 30000.

To access the file server, you can use the IP address of the nodes in your Kubernetes cluster and the NodePort that was assigned to the service. For example, if the IP address of one of your nodes is 10.0.0.1, you can access the file server at http://10.0.0.1:30000/.

## File Client
This is a Python client for downloading files from our file server and stressing it. It uses the requests library to make HTTP GET requests to the file server.

```shell
kubectl apply -f file-server/file-client.yaml
```