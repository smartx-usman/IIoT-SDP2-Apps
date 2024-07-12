# app.py

import logging
import os
import time
#import datetime
from datetime import datetime

import plotly.graph_objs as go
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Configure logging to output messages to the console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('MYSQL_URL',
                                                       'mysql+pymysql://username:password@hostname/database_name')
app.config['REFRESH_INTERVAL'] = int(os.environ.get('REFRESH_INTERVAL', 10))  # Default to 10 seconds
app.config['DATA_RANGE'] = int(os.environ.get('DATA_RANGE', 3600))  # Default to 1 hour
db = SQLAlchemy(app)


# Define your database model
class Temperature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    readingTS = db.Column(db.Integer)  # Assuming readingTS is in Unix timestamp format
    processTS = db.Column(db.Integer)  # Assuming processTS is in Unix timestamp format
    sensorID = db.Column(db.String(255))
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)


# Fetch sensorIDs from the database
def fetch_sensor_ids():
    sensor_ids = db.session.query(Temperature.sensorID).distinct().group_by(Temperature.sensorID).all()
    #sensor_ids = IIOT.query.distinct(IIOT.sensorID).all()
    return [sensor_id[0] for sensor_id in sensor_ids]


# Fetch data for a specific sensor from the database
def fetch_sensor_data(sensor_id):
    end_time = int(time.time())
    start_time = end_time - app.config['DATA_RANGE']
    query = text(f'SELECT readingTS, temperature, humidity FROM temperature WHERE sensorID = "{sensor_id}"  AND readingTS >= {start_time} AND readingTS <= {end_time} ORDER BY readingTS DESC')
    result = db.session.execute(query)
    timestamps = []
    temperatures = []
    humidities = []
    for row in result:
        # Convert readingTS from string to integer
        reading_ts = int(row.readingTS)
        timestamps.append(datetime.utcfromtimestamp(reading_ts))
        temperatures.append(row.temperature)
        humidities.append(row.humidity)
    return timestamps, temperatures, humidities


# Function to query temperature and humidity data from MySQL
def fetch_data():
    logger.info('Fetching data from MySQL...')
    end_time = int(time.time())
    start_time = end_time - app.config['DATA_RANGE']
    query = text(
        f'SELECT readingTS, temperature, humidity FROM temperature WHERE readingTS >= {start_time} AND readingTS <= {end_time} ORDER BY readingTS DESC')
    result = db.session.execute(query)
    timestamps = []
    temperatures = []
    humidities = []
    for row in result:
        # Convert readingTS from string to integer
        reading_ts = int(row.readingTS)
        timestamps.append(datetime.utcfromtimestamp(reading_ts))
        temperatures.append(row.temperature)
        humidities.append(row.humidity)
    logger.info('Data fetched successfully.')
    return timestamps, temperatures, humidities


# Function to create Plotly graph for temperature
def create_temperature_graph(timestamps, temperatures):
    logger.info('Creating temperature Plotly graph...')
    trace = go.Scatter(x=timestamps, y=temperatures, mode='lines+markers', name='Temperature')
    layout = go.Layout(title='Temperature Graph', xaxis=dict(title='Timestamp'), yaxis=dict(title='Temperature'))
    fig = go.Figure(data=[trace], layout=layout)
    logger.info('Temperature Plotly graph created.')
    return fig


# Function to create Plotly graph for humidity
def create_humidity_graph(timestamps, humidities):
    logger.info('Creating humidity Plotly graph...')
    trace = go.Scatter(x=timestamps, y=humidities, mode='lines+markers', name='Humidity')
    layout = go.Layout(title='Humidity Graph', xaxis=dict(title='Timestamp'), yaxis=dict(title='Humidity'))
    fig = go.Figure(data=[trace], layout=layout)
    logger.info('Humidity Plotly graph created.')
    return fig


# Route to display the web page with graphs
@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info('Rendering index page...')
    selected_sensor = None
    if request.method == 'POST':
        # Handle form submission
        selected_sensor = request.form.get('sensor')
    else:
        # Handle initial page load
        selected_sensor = fetch_sensor_ids()[0]
    sensor_ids = fetch_sensor_ids()
    #selected_sensor = request.form.get('sensor') if request.method == 'POST' else sensor_ids[0]
    timestamps, temperatures, humidities = fetch_sensor_data(selected_sensor)
    logger.info('Data fetched successfully.')
    logger.info('Sensor: %s, Temperatures: %s', selected_sensor, temperatures)

    #temperature_graph = create_temperature_graph(timestamps, temperatures).to_dict()
    #humidity_graph = create_humidity_graph(timestamps, humidities).to_dict()
    # Create Plotly graph for temperature
    temperature_trace = go.Scatter(x=timestamps, y=temperatures, mode='lines+markers', name='Temperature')

    # Create Plotly graph for humidity
    humidity_trace = go.Scatter(x=timestamps, y=humidities, mode='lines+markers', name='Humidity')

    temperature_graph = go.Figure(data=[temperature_trace])
    temperature_graph.update_layout(title='Temperature Graph', xaxis=dict(title='Timestamp'),
                                    yaxis=dict(title='Temperature'))

    humidity_graph = go.Figure(data=[humidity_trace])
    humidity_graph.update_layout(title='Humidity Graph', xaxis=dict(title='Timestamp'), yaxis=dict(title='Humidity'))

    # Convert Plotly graph objects to JSON format
    temperature_graph_json = temperature_graph.to_json()
    humidity_graph_json = humidity_graph.to_json()

    #logger.info('Temperature graph: %s', temperature_graph)
    #logger.info('Humidity graph: %s', humidity_graph)
    logger.info('Index page rendered successfully.')
    return render_template('index.html', sensor_ids=sensor_ids, selected_sensor=selected_sensor,
                           temperature_graph=temperature_graph_json, humidity_graph=humidity_graph_json,
                           refresh_interval=app.config['REFRESH_INTERVAL'], data_range=app.config['DATA_RANGE'],
                           database_source=app.config['SQLALCHEMY_DATABASE_URI'])


if __name__ == '__main__':
    from gunicorn.app.base import BaseApplication


    class FlaskApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application


    options = {
        'bind': '0.0.0.0:5000',
        'workers': 4,
        'timeout': 120
    }
    FlaskApplication(app, options).run()
