import mysql.connector

def db_connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Ww0500411097@",
        database="software"
    )
