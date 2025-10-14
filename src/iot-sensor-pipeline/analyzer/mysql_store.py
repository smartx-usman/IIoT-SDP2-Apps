import logging

import mysql.connector

from data_store import DataStore

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.WARN)


class MySQLStore(DataStore):
    def __init__(self, database_url):
        self.init_db(database_url)
        self.session, self.mysql_db = self.connect_db(database_url)

    def init_db(self, database_url):
        """Create database and tables"""
        mysql_db = mysql.connector.connect(
            host=database_url,
            user="root",
            password="root"
        )

        logging.info(mysql_db)
        session = mysql_db.cursor()
        try:
            session.execute("DROP DATABASE iiot")
        except Exception as ex:
            pass
        try:
            session.execute("CREATE DATABASE iiot")
        except Exception as ex:
            pass

        session.close

        mysql_db = mysql.connector.connect(host=database_url, user="root", password="root", database="iiot")
        session = mysql_db.cursor()
        session.execute(
            "CREATE TABLE temperature (id INT AUTO_INCREMENT PRIMARY KEY, readingTS VARCHAR(255), processTS VARCHAR(255), sensorID VARCHAR(255), temperature INT, humidity  FLOAT)")
        session.execute(
            "CREATE TABLE temperature_invalid (id INT AUTO_INCREMENT PRIMARY KEY, readingTS VARCHAR(255), processTS VARCHAR(255), sensorID VARCHAR(255), temperature INT, humidity  FLOAT)")
        session.close

    def connect_db(self, database_url):
        """Connect to MySQL database and return session and database"""
        mysql_db = mysql.connector.connect(host=database_url, user="root", password="root", database="iiot")
        session = mysql_db.cursor()

        return session, mysql_db

    def store_data(self, table, reading_ts, process_ts, sensor, temperature, humidity):
        """Store data in MySQL database"""
        sql = "INSERT INTO " + table + "(readingTS, ProcessTS, sensorID, temperature, humidity) VALUES(%s, %s, %s, %s, %s)"
        val = (reading_ts, process_ts, sensor, temperature, humidity)
        self.session.execute(sql, val)

        self.mysql_db.commit()
