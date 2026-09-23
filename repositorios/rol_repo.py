import json

from database.conexion import cursor_db
from models.rol import Rol


def _fila_a_rol(fila: dict) -> Rol:
    permisos = json.loads(fila["permisos"])
    rol = Rol(nombre=fila["nombre"], permisos=permisos)
    rol.id = fila["id"]
    return rol


def crear(rol: Rol) -> int:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "INSERT INTO roles (nombre, permisos) VALUES (%s, %s)",
            (rol.nombre, json.dumps(list(rol.permisos))),
        )
        rol.id = cursor.lastrowid
    return rol.id

def buscar_por_id(id_rol: int) -> Rol | None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM roles WHERE id = %s", (id_rol,))
        fila = cursor.fetchone()
    return _fila_a_rol(fila) if fila else None

def listar_todos() -> list[Rol]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM roles")
        filas = cursor.fetchall()
    return [_fila_a_rol(fila) for fila in filas] if filas else []

def buscar_por_nombre(nombre: str) -> Rol | None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM roles WHERE nombre = %s", (nombre,))
        fila = cursor.fetchone()
    return _fila_a_rol(fila) if fila else None

def actualizar(rol: Rol) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE roles SET nombre = %s, permisos = %s WHERE id = %s",
            (rol.nombre, json.dumps(list(rol.permisos)), rol.id),
        )