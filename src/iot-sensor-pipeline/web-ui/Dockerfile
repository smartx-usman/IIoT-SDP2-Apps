FROM python:3.12.3-slim

ENV DATABASE_URL="1"
ENV REFERESH_INTERVAL="0.5"
ENV DATA_RANGE="100"

ARG Pathdir="/web-ui"
RUN mkdir -p $Pathdir/templates
RUN mkdir -p $Pathdir/static

RUN apt -y update && apt install -y pkg-config python3-dev default-libmysqlclient-dev build-essential

RUN pip3 install Flask flask_sqlalchemy plotly mysqlclient
RUN pip3 install gunicorn

ADD app.py $Pathdir
ADD static/styles.css $Pathdir/static/
ADD templates/index.html $Pathdir/templates/

WORKDIR $Pathdir

#ENTRYPOINT ["python3", "app.py"]