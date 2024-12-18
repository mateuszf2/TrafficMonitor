import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

from pandas.core.computation.expr import intersection

connection = None
cursor = None

load_dotenv()

db_host = os.getenv('DB_HOST')
db_user = os.getenv("DB_USER")
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

def create_connection():
    try:
        connection = mysql.connector.connect(
            host = db_host,
            user = db_user,
            password = db_password,
            database = db_name
        )

        if connection.is_connected():
            print("Connected to MySQL database")
            db_info = connection.get_server_info()
            print("Server info: " + db_info)
            return connection

    except Error as e:
        print("Error while connecting to MySQL", e)
        return None

def close_connection(connection, cursor):
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")

def insert_nameOfPlace(name, city):
    connection = create_connection()
    cursor = None
    if connection:
        try:
            cursor = connection.cursor()
            query = "INSERT INTO nameOfPlace (name,city) VALUES (%s,%s);"
            cursor.execute(query, (name, city))
            connection.commit()
            print("Data about intersection added successfully.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            close_connection(connection, cursor)

def get_nameOfPlace():
    connection = create_connection()
    cursor = None
    #Data from table nameOfPlace that stores information about intersections in cities (name of intersection, city)
    intersections = None
    if connection:
        try:
            cursor = connection.cursor()
            query = "SELECT * FROM nameOfPlace;"
            cursor.execute(query)
            intersections = cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
        finally:
            close_connection(connection, cursor)

    return intersections