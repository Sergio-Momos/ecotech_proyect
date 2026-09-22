
from database.conexion import cursor_db
from repositorios import empleado_repo
from models.proyecto import Proyecto

def _fila_a_proyecto(fila: dict) -> Proyecto:
    proyecto = Proyecto(
        id=fila["id"],
        nombre=fila["nombre"],
        descripcion=fila["descripcion"],
        fecha_inicio=fila["fecha_inicio"],
        activo=bool(fila["activo"]),
    )
    for empleado in empleado_repo.listar_por_proyecto(fila["id"]):
        proyecto.asignar_empleado(empleado)
    return proyecto

def crear(proyecto: Proyecto) -> int:
    with cursor_db() as (cursor, _):
        cursor.execute(
            """
            INSERT INTO proyectos
                (nombre, descripcion, fecha_inicio)
            VALUES (%s, %s, %s)
            """,
            (
                proyecto.nombre,
                proyecto.descripcion,
                proyecto.fecha_inicio,
        )
        )
        proyecto.id = cursor.lastrowid   # ← sincroniza el objeto en memoria

    return proyecto.id

def listar_todos(incluir_inactivos: bool = False) -> list[Proyecto]:
    with cursor_db(dictionary=True) as (cursor, _):
        if incluir_inactivos:
            cursor.execute("SELECT * FROM proyectos")
        else:
            cursor.execute("SELECT * FROM proyectos WHERE activo = TRUE")
        filas = cursor.fetchall()
    return [_fila_a_proyecto(fila) for fila in filas]


def actualizar(proyecto: Proyecto) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE proyectos SET nombre = %s, descripcion = %s, fecha_inicio = %s WHERE id = %s",
            (
                proyecto.nombre,
                proyecto.descripcion,
                proyecto.fecha_inicio,
                proyecto.id,
            ),
        )


def asignar_empleado(proyecto_id: int, empleado_id: int) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "SELECT 1 FROM empleados_proyectos WHERE empleado_id = %s AND proyecto_id = %s",
            (empleado_id, proyecto_id),
        )
        if cursor.fetchone() is not None:
            raise ValueError(f"El empleado {empleado_id} ya participa en el proyecto {proyecto_id}.")
        cursor.execute(
            "INSERT INTO empleados_proyectos (empleado_id, proyecto_id) VALUES (%s, %s)",
            (empleado_id, proyecto_id),
        )

def quitar_empleado(proyecto_id: int, empleado_id: int) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "DELETE FROM empleados_proyectos WHERE empleado_id = %s AND proyecto_id = %s",
            (empleado_id, proyecto_id),
        )

def buscar_por_id(id_proyecto: int) -> Proyecto | None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM proyectos WHERE id = %s", (id_proyecto,))
        fila = cursor.fetchone()
    return _fila_a_proyecto(fila) if fila else None

def eliminar(id_proyecto: int) -> None:
    # Borrado lógico, no físico — preserva el historial de RegistroTiempo
    # asociado, que de otro modo quedaría huérfano o bloquearía el DELETE
    # por el ON DELETE RESTRICT de la FK.
    with cursor_db() as (cursor, _):
        cursor.execute("UPDATE proyectos SET activo = FALSE WHERE id = %s", (id_proyecto,))

