import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="admin",
    password="password",
    database="investManagment"
)

cursor = mydb.cursor()


def close_db():
    cursor.close()
    mydb.close()