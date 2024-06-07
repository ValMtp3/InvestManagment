import mysql.connector
from mysql.connector import connect, Error

def get_db_cursor():
    try:
        mydb = connect(
            host="localhost",
            port=3306,
            user="admin",
            password="password",
            database="investManagment"
        )
        return mydb, mydb.cursor()
    except Error as err:
        print(f"Erreur de connexion : {err}")
        return None, None

def close_db(mydb, cursor):
    try:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()
    except Error as e:
        print(f"Error closing the database: {e}")
