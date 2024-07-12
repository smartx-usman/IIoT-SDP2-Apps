FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN apt update && apt install -y iputils-ping tcpdump iproute2
RUN pip install --no-cache-dir -r requirements.txt

COPY coap-client.py .
COPY coap-server.py .

EXPOSE 5683/udp

CMD ["python", "coap-server.py"]