import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG


def obtener_conexion():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        raise ConnectionError(f"No se pudo conectar a la base de datos: {e}") from e


def probar_conexion() -> bool:
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return True
    finally:
        conexion.close()


probar_conexion()  # Llamada para probar la conexión al iniciar el módulo

    # contraseña acuerdate: Pablit0$hile