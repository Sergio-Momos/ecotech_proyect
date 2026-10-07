import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

from config import DB_PROFILES

_perfil_activo = None  # None -> usa el perfil "auth" por defecto


def establecer_perfil_activo(nombre_perfil: str) -> None:
    global _perfil_activo
    if nombre_perfil not in DB_PROFILES:
        raise ValueError(f"Perfil de BD desconocido: {nombre_perfil}")
    _perfil_activo = nombre_perfil


def limpiar_perfil_activo() -> None:
    global _perfil_activo
    _perfil_activo = None


def perfil_activo() -> str:
    return _perfil_activo or "auth"


def _config_activa() -> dict:
    return DB_PROFILES[perfil_activo()]


def obtener_conexion():
    try:
        print(f"[DEBUG] Conectando con perfil: {perfil_activo()}")
        return mysql.connector.connect(**_config_activa())
    except Error as e:
        raise ConnectionError(f"No se pudo conectar a la base de datos: {e}") from e


def probar_conexion(perfil: str | None = None) -> bool:
    """Prueba una conexión puntual. Sin argumento, prueba el perfil activo
    (o "auth" si no hay ninguno). Pasar un nombre de perfil permite probar
    cualquiera de los tres sin tener que activarlo primero."""
    config = DB_PROFILES[perfil] if perfil else _config_activa()
    conexion = mysql.connector.connect(**config)
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return True
    finally:
        conexion.close()


@contextmanager
def cursor_db(dictionary: bool = False):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=dictionary)
    try:
        yield cursor, conexion
        conexion.commit()
    finally:
        conexion.close()