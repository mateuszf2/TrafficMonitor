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

def get_data_for_inserting_video(crossroad_name,city_name,intersections):
    for intersection in intersections:
        if intersection[1]==crossroad_name and intersection[2]==city_name:
            return intersection[0]


def insert_video(idNameOfPlace, link, timeSet):
    connection = create_connection()
    cursor = None
    if connection:
        try:
            cursor = connection.cursor()
            query = "INSERT INTO video (id_nameOfPlace,link,timeSet) VALUES (%s,%s,%s);"
            cursor.execute(query, (idNameOfPlace,link,timeSet))
            connection.commit()
            print("Data about video added successfully.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            close_connection(connection, cursor)

def insert_trafficLanes(clickedPoints, idNameOfPlace):
    connection = create_connection()
    cursor = None
    if connection:
        for i in range(0, len(clickedPoints), 2):
            if i + 1 < len(clickedPoints):
                p1, p2 = clickedPoints[i], clickedPoints[i + 1]
                try:
                    cursor = connection.cursor()
                    query = "INSERT INTO trafficlanes (trafficLanesStartX,trafficLanesStartY,trafficLanesEndX,trafficLanesEndY,id_nameOfPlace) VALUES (%s,%s,%s,%s,%s);"
                    cursor.execute(query, (p1[0],p1[1],p2[0],p2[1],idNameOfPlace))
                    connection.commit()
                    print("Data about trafficlane added successfully.")
                except Error as e:
                    print(f"Error: {e}")

    close_connection(connection, cursor)

