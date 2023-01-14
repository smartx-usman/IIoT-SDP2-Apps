FROM python:3.8-slim

ENV SENSORS="1"

ARG Pathdir="/load"

RUN mkdir $Pathdir
RUN mkdir /data

RUN apt -y update && apt -y install --no-install-recommends stress

COPY system-load/stress-all.py $Pathdir

WORKDIR $Pathdir

#RUN chmod +x load-testing/disk-load.sh

#ENTRYPOINT ["python3", "actuate.py"]