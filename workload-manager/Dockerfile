# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app
#RUN mkdir /app/sensor-data-pipeline/kubernetes

# Copy the current directory contents into the container at /app
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl gnupg
RUN curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | tee /usr/share/keyrings/helm.gpg > /dev/null \
    && echo "deb [signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | tee /etc/apt/sources.list.d/helm-stable-debian.list > /dev/null \
    && apt-get update \
    && apt-get install -y helm

ADD workloads /app/workloads
ADD monitoring /app/monitoring
ADD templates /app/templates
ADD static /app/static
COPY app.py /app

#COPY ../sensor-data-pipeline/kubernetes/publisher-deployment-normal.yaml sensor-data-pipeline/kubernetes
#COPY ../sensor-data-pipeline/kubernetes/data-generator-job.yaml sensor-data-pipeline/kubernetes

# Make port 8000 available to the world outside this container
EXPOSE 9000

# Define environment variable
ENV NAME WorkloadManager

# Run app.py when the container launches
CMD ["python", "app.py"]
