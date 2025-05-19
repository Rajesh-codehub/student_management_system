import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_connection():
    try:
        # Retrieve database credentials from environment variables
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USERNAME', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'sms')
        }
        
        # Optional: Add additional connection parameters
        connection = mysql.connector.connect(
            **db_config,
            # Optional additional parameters
            # charset='utf8mb4',
            # connection_timeout=180
        )
        
        if connection.is_connected():
            print("Successfully connected to MySQL database")
            return connection
    
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def close_connection(connection):
    if connection and connection.is_connected():
        connection.close()
        print("MySQL connection closed")

# Optional: Add a connection test function
def test_connection():
    conn = create_connection()
    if conn:
        print("Connection successful!")
        close_connection(conn)
        return True
    else:
        print("Connection failed!")
        return False

# Can be used for debugging or as a standalone script
if __name__ == '__main__':
    test_connection()


# import mysql.connector
# from mysql.connector import Error

# def create_connection():
#     try:
#         connection = mysql.connector.connect(
#             host = "localhost",
#             username = "root",
#             password = "Rajubay@123",
#             database = "sms"
#         )

#         if connection.is_connected():
#             print("connected to mysql database")
#             return connection

#     except Error as e:
#         print(f"Error while connecting to mysql: {e}")
#         return None
    
# def close_connection(connection):
#     if connection and connection.is_connected():
#         connection.close()