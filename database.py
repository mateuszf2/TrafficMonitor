import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

connection = None
cursor = None

load_dotenv()

db_host = os.getenv('DB_HOST')
db_user = os.getenv("DB_USER")
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

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

        #Test query
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        record = cursor.fetchone()
        print("You are connected to database: " + record[0])

except Error as e:
    print("Error while connecting to MySQL", e)

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")