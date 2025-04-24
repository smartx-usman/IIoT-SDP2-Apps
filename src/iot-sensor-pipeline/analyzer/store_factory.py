import logging

from cassandra_store import CassandraStore
from mysql_store import MySQLStore
from file_store import FileStore


def get_store(datastore, database_url, data_file_normal, data_file_anomalous, tracer):
    table_valid = 'temperature'
    table_invalid = 'temperature_invalid'

    if datastore == 'cassandra':
        with tracer.start_as_current_span("store-connector") as child_level1_span4:
            child_level1_span4.set_attribute('store_name', datastore)
            store = CassandraStore(database_url=database_url)
    elif datastore == 'mysql':
        with tracer.start_as_current_span("store-connector") as child_level1_span4:
            child_level1_span4.set_attribute('store_name', datastore)
            store = MySQLStore(database_url=database_url)
    elif datastore == 'file':
        with tracer.start_as_current_span("store-connector") as child_level1_span4:
            child_level1_span4.set_attribute('store_name', datastore)
            store = FileStore()
            table_valid, table_invalid = store.open_file(
                data_file_normal=data_file_normal,
                data_file_anomalous=data_file_anomalous
            )
    else:
        store = None
        logging.info('message=Data is not going to be saved.')

    return store, table_valid, table_invalid
