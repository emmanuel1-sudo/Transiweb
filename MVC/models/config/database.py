import mysql.connector

def conectar_bd():
    conexion = mysql.connector.connect(
        host="127.0.0.1",
        port=3307,
        user="root",
        password="",
        database="transiweb",
        charset="utf8mb4"
    )
    return conexion
