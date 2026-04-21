FROM python:3.14-slim

ENV SENSORS="1"

ARG Pathdir="/load"

RUN mkdir $Pathdir
RUN mkdir /data

#RUN apt -y update && apt -y install --no-install-recommends stress \
RUN pip3 install locust

COPY system-load/stress-all.py $Pathdir
COPY system-load/locustfile.py $Pathdir

WORKDIR $Pathdir

#RUN chmod +x load-testing/disk-load.sh

#ENTRYPOINT ["python3", "actuate.py"]