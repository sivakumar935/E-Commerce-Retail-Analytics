import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "sivakumar",
    "database": "cart2insights"
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)
