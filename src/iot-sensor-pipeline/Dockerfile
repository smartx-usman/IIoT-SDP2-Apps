FROM python:3.9.16-slim

ENV SENSORS="1"
ENV MESSAGE_DELAY="0.5"

ARG Pathdir="/mqtt"

RUN apt -y update && apt -y install --no-install-recommends build-essential stress mosquitto-clients

RUN mkdir $Pathdir
RUN mkdir /data

COPY requirements.txt .

#RUN apk update && apk add build-essential
#RUN /usr/local/bin/python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt

ADD generator $Pathdir/generator
ADD publisher $Pathdir/publisher
ADD subscriber $Pathdir/subscriber
ADD analyzer $Pathdir/analyzer
ADD actuator $Pathdir/actuator

WORKDIR $Pathdir

#RUN chmod +x load-testing/disk-load.sh
#ENTRYPOINT ["python3", "actuate.py"]