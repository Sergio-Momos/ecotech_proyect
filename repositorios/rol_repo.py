import json

from database.conexion import cursor_db
from models.rol import Rol


def _fila_a_rol(fila: dict) -> Rol:
    """Reconstruye un Rol; sus permisos se almacenan como JSON en MySQL."""
    permisos = json.loads(fila["permisos"])
    rol = Rol(nombre=fila["nombre"], perfil_bd=fila["perfil_bd"], permisos=permisos)
    rol._id = fila["id"]
    return rol

def crear(rol: Rol) -> int:
    """Inserta un rol y copia el id autogenerado al objeto recibido."""
    with cursor_db() as (cursor, _):
        cursor.execute(
            "INSERT INTO roles (nombre, perfil_bd, permisos) VALUES (%s, %s, %s)",
            (rol._nombre, rol._perfil_bd, json.dumps(list(rol._permisos))),
        )
        rol._id = cursor.lastrowid
    return rol._id

def buscar_por_id(id_rol: int) -> Rol | None:
    """Busca un rol por id; devuelve None si no existe."""
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM roles WHERE id = %s", (id_rol,))
        fila = cursor.fetchone()
    return _fila_a_rol(fila) if fila else None

def listar_todos() -> list[Rol]:
    """Lista todos los roles disponibles y convierte sus filas a objetos."""
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM roles")
        filas = cursor.fetchall()
    return [_fila_a_rol(fila) for fila in filas]

def buscar_por_nombre(nombre: str) -> Rol | None:
    """Busca un rol por nombre, por ejemplo RRHH o TI."""
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM roles WHERE nombre = %s", (nombre,))
        fila = cursor.fetchone()
    return _fila_a_rol(fila) if fila else None

def actualizar(rol: Rol) -> None:
    """Actualiza nombre, perfil de BD y permisos serializados como JSON."""
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE roles SET nombre = %s, perfil_bd = %s, permisos = %s WHERE id = %s",
            (rol._nombre, rol._perfil_bd, json.dumps(list(rol._permisos)), rol._id),
        )
