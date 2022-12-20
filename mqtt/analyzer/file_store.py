import logging
import os

from data_store import DataStore

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.WARN)


class FileStore(DataStore):
    def connect_db(self):
        pass

    @staticmethod
    def open_file(data_file_normal, data_file_anomalous):
        """Remove old data file from persistent volume"""
        if os.path.exists(data_file_normal):
            os.remove(data_file_normal)
            logging.info('Removed old file from the PV.')
        else:
            logging.info('The file does not exist.')

        if os.path.exists(data_file_anomalous):
            os.remove(data_file_anomalous)
            logging.info('Removed old file from the PV.')
        else:
            logging.info('The file does not exist.')

        # Open data file for writing
        try:
            temperature_file_normal = open(data_file_normal, "a")
        except Exception as ex:
            logging.error(f'Exception while opening file {temperature_file_normal}.', exc_info=True)

        try:
            temperature_file_anomalous = open(data_file_anomalous, "a")
        except Exception as ex:
            logging.error(f'Exception while opening file {temperature_file_anomalous}.', exc_info=True)
        return temperature_file_normal, temperature_file_anomalous

    def store_data(self, session, file_handler, reading_ts, process_ts, sensor, temperature, humidity):
        file_handler.write(
            str(reading_ts) + "," + str(process_ts) + "," + sensor + "," + str(temperature) + "," + str(humidity) + "\n")
