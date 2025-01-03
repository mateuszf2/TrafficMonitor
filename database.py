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


def insert_video(idNameOfPlace, link, timeSet):
    connection = create_connection()
    cursor = None
    insertedId = None
    if connection:
        try:
            cursor = connection.cursor()
            query = "INSERT INTO video (id_nameOfPlace,link,timeSet) VALUES (%s,%s,%s);"
            cursor.execute(query, (idNameOfPlace,link,timeSet))
            connection.commit()

            insertedId = cursor.lastrowid
            print("Data about video added successfully.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            close_connection(connection, cursor)
            return insertedId

def insert_trafficLanes(clickedPoints, idNameOfPlace):
    connection = create_connection()
    cursor = None
    listOfIdTrafficLanes = []
    if connection:
        try:
            for i in range(0, len(clickedPoints), 2):
                if i + 1 < len(clickedPoints):
                    p1, p2 = clickedPoints[i], clickedPoints[i + 1]

                    cursor = connection.cursor()
                    query = "INSERT INTO trafficlanes (trafficLanesStartX,trafficLanesStartY,trafficLanesEndX,trafficLanesEndY,id_nameOfPlace) VALUES (%s,%s,%s,%s,%s);"
                    cursor.execute(query, (p1[0],p1[1],p2[0],p2[1],idNameOfPlace))

                    listOfIdTrafficLanes.append(cursor.lastrowid)
                    print("Data about trafficlane added successfully.")
            connection.commit()
        except Error as e:
            print(f"Error: {e}")
            connection.rollback()

    close_connection(connection, cursor)
    return listOfIdTrafficLanes

def insert_signalLights(rightClickedPoints, thirdClickedPoints, idNameOfPlace):
    connection = create_connection()
    cursor = None
    if connection:
            for i in range(0, len(rightClickedPoints), 2):
                if i + 1 < len(rightClickedPoints):
                    p1, p2 = rightClickedPoints[i], rightClickedPoints[i + 1]
                    p3 = thirdClickedPoints[i // 2]
                    try:
                        cursor = connection.cursor()
                        query = "INSERT INTO signalLights (stopLineStartX, stopLineStartY, stopLineEndX, stopLineEndY, signalX, signalY, id_nameOfPlace) VALUES (%s, %s, %s, %s, %s, %s, %s);"
                        cursor.execute(query, (p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], idNameOfPlace))
                        connection.commit()
                        print("Data about signalLights added successfully.")
                    except Error as e:
                        print(f"Error: {e}")
    close_connection(connection, cursor)

def insert_carGrouped(idVideo, carsGroupedByArr, listOfIdTrafficLanes,carStartTimes):
    connection = create_connection()
    cursor = None
    if connection:
        try:
            for i, group in enumerate(carsGroupedByArr):
                for car in group:
                    id, cy = car
                    #print(f"IdTrafficLane: {listOfIdTrafficLanes[i]} CarID: {id}")
                    idTrafficLanes = listOfIdTrafficLanes[i]

                    cursor = connection.cursor()
                    if carStartTimes[id]!=-1:
                        query = "INSERT INTO car(id, id_video, id_trafficLanes,startTime) VALUES(%s, %s, %s,%s)"
                        cursor.execute(query, (id, idVideo, idTrafficLanes,carStartTimes[id]))
                    else:
                        query = "INSERT INTO car(id, id_video, id_trafficLanes) VALUES(%s, %s, %s)"
                        cursor.execute(query, (id, idVideo, idTrafficLanes))
            connection.commit()
            print("Data about car added successfully.")
        except Error as e:
            print(f"Error: {e}")
            connection.rollback()

    close_connection(connection, cursor)

def insert_carNotGrouped(idVideo, allCarsId):
    connection = create_connection()
    cursor = None
    if connection:
        try:
            for carId in allCarsId:
                cursor = connection.cursor()

                query = "INSERT INTO car(id, id_video) VALUES(%s, %s)"
                cursor.execute(query, (carId, idVideo))
            connection.commit()
            print("Data about car added successfully.")
        except Error as e:
            print(f"Error: {e}")
            connection.rollback()

    close_connection(connection, cursor)

def insert_speedsOfCars(idVideo,carSpeeds):
    connection = create_connection()
    cursor = None
    if connection:
        try:
            # Iterate through the defaultdict
            for carId, speeds in carSpeeds.items():
                second=0
                for speed in speeds:
                    cursor = connection.cursor()
                    second+=1
                    query = "INSERT INTO speedOfCar(id_car, id_video,secondOfVideo,speed) VALUES(%s,%s,%s,%s)"
                    cursor.execute(query, (carId, idVideo,second,speed))

            connection.commit()
            print("Data about cars speeds added successfully.")
        except Error as e:
            print(f"Error: {e}")
            connection.rollback()

    close_connection(connection, cursor)

def insert_distancesBetweenCars(idVideo,distancesBetweenCars):
    connection = create_connection()
    cursor = None
    if connection:
        try:
            # Iterate through the defaultdict
            for (carId1,carId2), distances in distancesBetweenCars.items():
                second=0
                for distance in distances:
                    cursor = connection.cursor()
                    second+=1
                    query = "INSERT INTO distanceofcar(id_car1,id_car2, id_video1,id_video2,secondOfVideo,length) VALUES(%s,%s,%s,%s,%s,%s)"
                    cursor.execute(query, (carId1,carId2, idVideo,idVideo, second,distance))

            connection.commit()
            print("Data about distances between cars added successfully.")
        except Error as e:
            print(f"Error: {e}")
            connection.rollback()

    close_connection(connection, cursor)


