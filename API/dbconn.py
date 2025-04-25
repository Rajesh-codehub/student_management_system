import mysql.connector
from mysql.connector import Error

def create_connection():
    try:
        connection = mysql.connector.connect(
            host = "localhost",
            username = "root",
            password = "Rajubay@123",
            database = "sms"
        )

        if connection.is_connected():
            print("connected to mysql database")
            return connection

    except Error as e:
        print(f"Error while connecting to mysql: {e}")
        return None
    
def close_connection(connection):
    if connection and connection.is_connected():
        connection.close()