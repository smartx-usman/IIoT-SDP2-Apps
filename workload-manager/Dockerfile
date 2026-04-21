FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt /app

RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg \
    && curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 \
    && chmod 700 get_helm.sh && ./get_helm.sh \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y curl gnupg \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* get_helm.sh

COPY workloads /app/workloads
COPY monitoring /app/monitoring
COPY templates /app/templates
COPY static /app/static
COPY app /app/app
COPY config.py /app
COPY run.py /app

#RUN useradd -m workloadman
#USER workloadman

EXPOSE 9000

ENV NAME WorkloadManager

CMD ["python", "run.py"]
