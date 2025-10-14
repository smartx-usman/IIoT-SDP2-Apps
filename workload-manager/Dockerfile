FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl gnupg
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 \
    && chmod 700 get_helm.sh \
    && ./get_helm.sh
ADD workloads /app/workloads
ADD monitoring /app/monitoring
ADD templates /app/templates
ADD static /app/static
ADD app /app/app

COPY config.py /app
COPY run.py /app

EXPOSE 9000

ENV NAME WorkloadManager

CMD ["python", "run.py"]
