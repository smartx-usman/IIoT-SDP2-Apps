FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app

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
ADD app /app/app

COPY app.py /app
COPY config.py /app
COPY run.py /app

EXPOSE 9000

ENV NAME WorkloadManager

CMD ["python", "run.py"]
