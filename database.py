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

def insert_carGrouped(idVideo, carsGroupedByArr, listOfIdTrafficLanes,carStartTimes, carsHasCrossedLight):
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
                        query = "INSERT INTO car(id, id_video, id_trafficLanes,startTime, ifRed) VALUES(%s, %s, %s,%s,%s)"
                        cursor.execute(query, (id, idVideo, idTrafficLanes,carStartTimes[id], carsHasCrossedLight.get(id)))
                    else:
                        query = "INSERT INTO car(id, id_video, id_trafficLanes, ifRed) VALUES(%s, %s, %s,%s)"
                        cursor.execute(query, (id, idVideo, idTrafficLanes, carsHasCrossedLight.get(id)))
            connection.commit()
            print("Data about car added successfully.")
        except Error as e:
            print(f"Error: {e}")
            connection.rollback()

    close_connection(connection, cursor)

def insert_carNotGrouped(idVideo, allCarsId,carsHasCrossedLight):
    connection = create_connection()
    cursor = None
    if connection:
        try:
            for carId in allCarsId:
                cursor = connection.cursor()

                query = "INSERT INTO car(id, id_video,ifRed) VALUES(%s, %s, %s)"
                cursor.execute(query, (carId, idVideo, carsHasCrossedLight.get(carId)))
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
        finally:
            close_connection(connection, cursor)


def get_signallights(name, city):
    connection = create_connection()
    cursor = None
    #Data from table nameOfPlace that stores information about intersections in cities (name of intersection, city)
    intersections = None
    if connection:
        try:
            cursor = connection.cursor()
            query = "select * from signallights s join nameofplace n on s.id_nameOfPlace=n.id where name=%s and city=%s;"
            cursor.execute(query, (name,city))
            signallights = cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
        finally:
            close_connection(connection, cursor)

    return signallights

def get_trafficlanes(name, city):
    connection = create_connection()
    cursor = None
    #Data from table nameOfPlace that stores information about intersections in cities (name of intersection, city)
    intersections = None
    if connection:
        try:
            cursor = connection.cursor()
            query = "select * from trafficlanes t join nameofplace n on t.id_nameOfPlace=n.id where name=%s and city=%s;"
            cursor.execute(query, (name,city))
            trafficlanes = cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
        finally:
            close_connection(connection, cursor)

    return trafficlanes

def delete_trafficLanes_cascade(idNameOfPlace):
    connection = create_connection()
    cursor = None
    if connection:
        try:
            cursor = connection.cursor()

            # Usunięcie rekordów z speedOfCar
            query = """
                DELETE FROM speedOfCar 
                WHERE (id_car, id_video) IN (
                    SELECT id, id_video FROM car WHERE id_trafficLanes IN (
                        SELECT id FROM trafficLanes WHERE id_nameOfPlace = %s
                    )
                );
            """
            cursor.execute(query, (idNameOfPlace,))

            # Usunięcie rekordów z distanceOfCar
            query = """
                DELETE FROM distanceOfCar 
                WHERE (id_car1, id_video1) IN (
                    SELECT id, id_video FROM car WHERE id_trafficLanes IN (
                        SELECT id FROM trafficLanes WHERE id_nameOfPlace = %s
                    )
                )
                OR (id_car2, id_video2) IN (
                    SELECT id, id_video FROM car WHERE id_trafficLanes IN (
                        SELECT id FROM trafficLanes WHERE id_nameOfPlace = %s
                    )
                );
            """
            cursor.execute(query, (idNameOfPlace, idNameOfPlace))

            # Usunięcie rekordów z car
            query = """
                DELETE FROM car 
                WHERE id_trafficLanes IN (
                    SELECT id FROM trafficLanes WHERE id_nameOfPlace = %s
                );
            """
            cursor.execute(query, (idNameOfPlace,))

            # Usunięcie samych traffic lanes
            query = "DELETE FROM trafficLanes WHERE id_nameOfPlace = %s;"
            cursor.execute(query, (idNameOfPlace,))

            # Usunięcie samych signal lights
            query = "DELETE FROM signallights WHERE id_nameOfPlace = %s;"
            cursor.execute(query, (idNameOfPlace,))

            query = """
                DELETE FROM speedOfCar 
                WHERE (id_car, id_video) IN (
                    SELECT id, id_video FROM car WHERE id_video IN (
                        SELECT id FROM video WHERE id_nameOfPlace = %s
                    )
                );
            """
            cursor.execute(query, (idNameOfPlace,))

            query = """
                DELETE FROM car 
                WHERE id_video IN (
                    SELECT id FROM video WHERE id_nameOfPlace = %s
                );
            """
            cursor.execute(query, (idNameOfPlace,))

            query = "DELETE FROM video WHERE id_nameOfPlace = %s;"
            cursor.execute(query, (idNameOfPlace,))

            connection.commit()
            print("All related traffic lanes and their dependencies have been deleted successfully.")

        except Error as e:
            print(f"Error: {e}")
            connection.rollback()

        finally:
            close_connection(connection, cursor)



