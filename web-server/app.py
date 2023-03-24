import logging
import os
import subprocess
import sys
import time
import uuid
from random import randint
from threading import Thread

import numpy as np
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from flask import Flask, request, jsonify, abort
from flask_mysqldb import MySQL
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from waitress import serve

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

resource = Resource(attributes={
    SERVICE_NAME: "flask-web-service"
})

provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger-collector.observability.svc.cluster.local:4317", insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

app = Flask(__name__)
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'flask'

mysql = MySQL(app)


@app.route("/roll")
def roll():
    sides = int(request.args.get('sides'))
    rolls = int(request.args.get('rolls'))
    logging.info('Roll request completed.')
    return roll_sum(sides, rolls)


def roll_sum(sides, rolls):
    with tracer.start_as_current_span("roll_sum") as rollspan:
        # span = trace.get_current_span()
        rollspan.set_attribute('my-tag', 10)
        sum = 0
        for r in range(0, rolls):
            result = randint(1, sides)
            # rollspan.set_attribute('sum', result)
            rollspan.add_event("log", {
                "roll.sides": sides,
                "roll.result": result,
            })
            sum += result
        return str(sum)


@app.route("/multispan")
def multi_span():
    # Create a new span to track some work
    with tracer.start_as_current_span("parent") as parent_span:
        time.sleep(1)
        parent_span.set_attribute('my-tag', 'parent')

        # Create a nested span to track nested work
        with tracer.start_as_current_span("child") as child_span:
            child_span.set_attribute('my-tag', 'child')
            time.sleep(2)
            # the nested span is closed when it's out of scope

        # Now the parent span is the current span again
        time.sleep(1)
    return 'Finished'


@app.route("/matrix")
def matrix():
    with tracer.start_as_current_span("matrix") as parent_span:
        start_dt = time.time()
        operation = request.args.get('operation')
        parent_span.set_attribute('operation', operation)

        if operation == 'multiply':
            matrix_multiply()
        elif operation == 'add':
            logging.ERROR(f'{operation} operation is not yet implemented.')
            abort(400, description=f"{operation} operation is not yet implemented.")
        else:
            abort(400, description=f"{operation} operation is not valid.")

        end_dt = time.time()
        latency = end_dt - start_dt
        parent_span.set_attribute('e2e_latency', latency)

        return 'Finished execution successfully.'


def matrix_multiply():
    # Create a new span to track some work
    start = int(request.args.get('start'))
    end = int(request.args.get('end'))
    rows = int(request.args.get('rows'))
    cols = int(request.args.get('cols'))

    with tracer.start_as_current_span("matrix-data-op") as child_span1:
        child_span1.set_attribute('start_range', start)
        child_span1.set_attribute('end_range', end)
        matrix_a = np.random.randint(start, end, size=(rows, cols))
        matrix_b = np.random.randint(start, end, size=(rows, cols))

    with tracer.start_as_current_span("matrix-multiply-op") as child_span2:
        result = np.matmul(matrix_a, matrix_b)
        child_span2.set_attribute('rows', rows)
        child_span2.set_attribute('cols', cols)
    logging.info('Matrix multiplication request completed.')


@app.route("/sorting")
def sorting():
    # Create a new span to track some work
    with tracer.start_as_current_span("sorting") as parent_span:
        start_dt = time.time()
        kind = request.args.get('kind')
        start = int(request.args.get('start'))
        end = int(request.args.get('end'))
        size = int(request.args.get('size'))
        store = request.args.get('store')

        data = generate_data(start=start, end=end, size=size)
        sort_data(data=data, kind=kind, store=store)

        # Now the parent span is the current span again
        end_dt = time.time()
        latency = end_dt - start_dt
        parent_span.set_attribute('e2e_latency', latency)
        logging.info('Data sorting request completed.')
    return 'Request completed.'


def generate_data(start, end, size):
    with tracer.start_as_current_span("generate-data-op") as child_span1:
        child_span1.set_attribute('start_range', start)
        child_span1.set_attribute('end_range', end)
        child_span1.set_attribute('size', size)
        data = np.random.randint(start, end, size=size)
        return data


def sort_data(data, kind, store):
    with tracer.start_as_current_span("sort-data-op") as child_span2:
        child_span2.set_attribute('kind', kind)
        sorted_data = np.sort(data, axis=0, kind=kind)
        if store == 'mysql':
            save_data_mysql(data=sorted_data, kind=kind)
        else:
            save_data_cassandra(data=sorted_data, kind=kind)


def save_data_mysql(data, kind):
    """Save data to MySQL"""
    with tracer.start_as_current_span("save-data-op") as child_span3:
        child_span3.set_attribute('store', 'MySQL')
        child_span3.set_attribute('table', 'sorted_data')
        server = request.remote_addr
        client = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ['REMOTE_ADDR'])
        namespace = request.args.get('namespace')
        app.config['MYSQL_HOST'] = f'mysql.{namespace}.svc.cluster.local'

        # Creating a connection cursor
        cursor = mysql.connection.cursor()

        # Executing SQL Statements

        # try:
        #    cursor.execute(''' DROP TABLE sorted_data ''')
        # except Exception as error:
        #    logging.warning("Table does not exist: {}".format(error))

        try:
            cursor.execute(
                ''' CREATE TABLE sorted_data(
                id INT AUTO_INCREMENT PRIMARY KEY, 
                server VARCHAR(255),
                client VARCHAR(255), 
                algorithm VARCHAR(255),
                value INT UNSIGNED) ''')
        except Exception as error:
            pass

        try:
            for value in data:
                cursor.execute(''' INSERT INTO sorted_data(server, client, algorithm, value) VALUES(%s, %s, %s, %s) ''',
                               (server, client, kind, value))
        except Exception as error:
            logging.error("Data is not inserted: {}".format(error))

        # Saving the Actions performed on the DB
        mysql.connection.commit()

        # Closing the cursor
        cursor.close()


def save_data_cassandra(data, kind):
    """Save data to Cassandra"""
    with tracer.start_as_current_span("save-data-op") as child_span3:
        table_name = 't' + str(uuid.uuid1().hex)
        keyspace = request.args.get('database')
        namespace = request.args.get('namespace')
        logging.info(f'Table name is {table_name}.')
        child_span3.set_attribute('store', 'Cassandra')
        child_span3.set_attribute('table', table_name)

        server = request.remote_addr
        client = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ['REMOTE_ADDR'])

        auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandrapass')
        cluster = Cluster([f'cassandra-0.cassandra-headless.{namespace}.svc.cluster.local'],
                          auth_provider=auth_provider,
                          protocol_version=5)

        try:
            session = cluster.connect()
        except Exception as error:
            logging.error("Problem while connecting to Casandra. {}".format(error))

        try:
            session.execute(
                "CREATE KEYSPACE IF NOT EXISTS " + keyspace + " WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };")
            logging.info(f'Created keyspace {keyspace}.')
        except Exception as ex:
            pass

        try:
            session = cluster.connect(keyspace)
            logging.info(f'Connected to keyspace {keyspace}.')
        except Exception as ex:
            logging.error(f'Problem while connecting to Casandra.')

        create_table_query = f'''
        CREATE TABLE {table_name} (
        id int PRIMARY KEY,
        server text,
        client text,
        algorithm text,
        value int
        );'''

        try:
            session.execute(create_table_query)
            logging.info(f'Create table {table_name} success.')
        except Exception as ex:
            pass

        try:
            row_id = 1
            for value in data:
                session.execute(
                    f"""
                    INSERT INTO {table_name} (id, server, client, algorithm, value) VALUES(%s, %s, %s, %s, %s)
                    """,
                    (row_id, server, client, kind, int(value))
                )
                row_id = row_id + 1
        except Exception as error:
            logging.error("Data is not inserted: {}".format(error))
            abort(500, description="Data is not inserted")


@app.route("/normal_load")
def normal_load():
    hdd = int(request.args.get('hdd'))
    io = int(request.args.get('io'))
    vm = int(request.args.get('vm'))
    cpu = int(request.args.get('cpu'))
    timeout = int(request.args.get('timeout'))

    # Create a new span to track some work
    with tracer.start_as_current_span("parent") as parent_span:
        proc = subprocess.Popen(
            "stress --hdd " + str(hdd) + " --io " + str(io) + " --vm " + str(vm) + " --cpu " + str(
                cpu) + " --timeout " + str(timeout) + "s",
            stdout=subprocess.PIPE,
            shell=True)
        parent_span.set_attribute('hdd', hdd)
        parent_span.set_attribute('io', io)
        parent_span.set_attribute('vm', vm)
        parent_span.set_attribute('cpu', cpu)
        parent_span.set_attribute('timeout', timeout)

    try:
        outs, errs = proc.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        proc.kill()
        abort(500, description="The timeout is expired!")

    if errs:
        abort(500, description=errs.decode('utf-8'))

    return 'Finished'


@app.route("/drop_database")
def drop_database():
    keyspace = request.args.get('database')
    namespace = request.args.get('namespace')
    auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandrapass')
    cluster = Cluster([f'cassandra-0.cassandra-headless.{namespace}.svc.cluster.local'],
                      auth_provider=auth_provider,
                      protocol_version=5)

    try:
        session = cluster.connect()
    except Exception as ex:
        logging.error(f'Problem while connecting to Cassandra.')

    try:
        session.execute(f'DROP keyspace IF EXISTS {keyspace};')
        logging.info(f'Keyspace is dropped successfully.')
    except Exception as ex:
        logging.ERROR(f'Flask keyspace not dropped.')

    return 'Keyspace is dropped successfully.'


@app.route("/create_database")
def create_database():
    keyspace = request.args.get('database')
    namespace = request.args.get('namespace')
    auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandrapass')
    cluster = Cluster([f'cassandra-0.cassandra-headless.{namespace}.svc.cluster.local'],
                      auth_provider=auth_provider,
                      protocol_version=5)

    try:
        session = cluster.connect()
    except Exception as ex:
        logging.error(f'Problem while connecting to Casandra.')

    try:
        session.execute(
            "CREATE KEYSPACE IF NOT EXISTS " + keyspace + " WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };")
        logging.info(f'Created keyspace {keyspace}.')
    except Exception as ex:
        logging.WARNING(f'{keyspace} keyspace already exists.')

    return 'Keyspace is created successfully.'


@app.errorhandler(500)
def server_error(error):
    return jsonify(success=False, message=error.description), 500


@app.errorhandler(400)
def server_error(error):
    return jsonify(success=False, message=error.description), 400


def stress_task():
    time.sleep(stress_initial_delay)
    command = "stress"

    if int(vm) <= 0 and int(cpu) <= 0 and int(hdd) <= 0 and int(io) <= 0:
        logging.error('Invalid stress options provided. Application is exiting.')
        sys.exit()
    else:
        command = command + " --cpu " + str(cpu) if int(cpu) >= 1 else command
        command = command + " --vm " + str(vm) + " --vm-bytes " + str(vm_bytes) if int(vm) >= 1 else command
        command = command + " --hdd " + str(hdd) if int(hdd) >= 1 else command
        command = command + " --io " + str(io) if int(io) >= 1 else command

        command = command + " --timeout " + str(stress_timeout)
    # command = "stress  --cpu " + str(cpu) + " --vm " + str(vm) + " --vm-bytes " + str(vm_bytes) + " --hdd " + str(
    #    hdd) + " --io " + str(io) + " --timeout " + str(stress_timeout)

    while True:
        logging.info('Stress test Started.')
        logging.info(f'Stress command: [{command}].')

        process = subprocess.Popen(
            [command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            universal_newlines=True)
        stdout, stderr = process.communicate()
        print(stdout)
        logging.info('Stress test Ended.')
        time.sleep(idle_timeout)


# app.run((host="0.0.0.0")
if __name__ == "__main__":
    hdd = os.environ['STRESS_HDD']
    io = os.environ['STRESS_IO']
    vm = os.environ['STRESS_VM']
    cpu = os.environ['STRESS_CPU']
    vm_bytes = os.environ['STRESS_VM_BYTES']
    stress_timeout = os.environ['STRESS_TIMEOUT']
    idle_timeout = int(os.environ['IDLE_TIMEOUT'])
    stress_initial_delay = int(os.environ['STRESS_INIT_DELAY'])
    stress = (os.environ['STRESS_APP']).capitalize()
    total_threads = int(os.environ['FLASK_THREADS'])

    if (stress == "True"):
        thread = Thread(target=stress_task)
        thread.daemon = True
        thread.start()

    serve(app, host="0.0.0.0", port=5000, connection_limit=1024, threads=total_threads)
    # app.run(host="0.0.0.0", debug=True)
    # thread.join()
# curl 'http://127.0.0.1:5000/roll?sides=10&rolls=5'
# curl 'http://127.0.0.1:5000/multispan'
# curl 'http://127.0.0.1:5000/normal_load?hdd=1&io=1&vm=1&cpu=1&timeout=60'
