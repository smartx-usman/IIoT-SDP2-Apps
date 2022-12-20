import logging

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster

from data_store import DataStore

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.WARN)


class CassandraStore(DataStore):
    def __init__(self, database_url):
        self.session = self.connect_db(database_url)

    def connect_db(self, database_url):
        """Create Cassandra connection"""
        logging.info('Database URL: '+database_url)
        auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandrapass')
        cluster = Cluster([database_url],
                          auth_provider=auth_provider,
                          protocol_version=5)

        try:
            session = cluster.connect()
        except Exception as ex:
            logging.error(f'Problem while connecting to Casandra.')

        try:
            session.execute(f'DROP keyspace IF EXISTS iiot;')
            session.execute(
                "create keyspace iiot with replication={'class': 'SimpleStrategy', 'replication_factor' : 1};")
        except Exception as ex:
            logging.error(f'Problem while dropping or creating iiot keyspace.')

        try:
            session = cluster.connect('iiot')
        except Exception as ex:
            logging.error(f'Problem while connecting to Casandra.')

        query_temperature_valid_table = '''
        create table temperature (
           readingTS timestamp,
           processTS timestamp,
           sensorID text,
           temperature int,
           humidity float,
           primary key(readingTS)
        );'''
        query_temperature_invalid_table = '''
        create table temperature_invalid (
           readingTS timestamp,
           processTS timestamp,
           sensorID text,
           temperature int,
           humidity float,
           primary key(readingTS)
        );'''

        try:
            session.execute(query_temperature_valid_table)
        except Exception as ex:
            logging.info(f'Table already exists. Not creating.')

        try:
            session.execute(query_temperature_invalid_table)
        except Exception as ex:
            logging.info(f'Table already exists. Not creating.')

        return session

    def store_data(self, table, reading_ts, process_ts, sensor, temperature, humidity):
        """Save data to cassandra database"""
        self.session.execute(
            f"""
                INSERT INTO {table} (readingTS, ProcessTS, sensorID, temperature, humidity) VALUES(%s, %s, %s, %s, %s)
                """,
            (reading_ts, process_ts, sensor, temperature, humidity)
        )
