from database.conexion import cursor_db
from repositorios import empleado_repo, proyecto_repo
from models.registro_tiempo import RegistroTiempo


def _fila_a_registro(fila: dict) -> RegistroTiempo:
    empleado = empleado_repo.buscar_por_id(fila["empleado_id"])
    proyecto = proyecto_repo.buscar_por_id(fila["proyecto_id"])
    registro = RegistroTiempo(
        fecha=fila["fecha"],
        horas_trabajadas=float(fila["horas_trabajadas"]),
        descripcion=fila["descripcion"],
        empleado=empleado,
        proyecto=proyecto,
    )
    registro.id = fila["id"]
    return registro


def crear(registro: RegistroTiempo) -> int:
    with cursor_db() as (cursor, _):
        cursor.execute(
            """
            INSERT INTO registros_tiempo
                (fecha, horas_trabajadas, descripcion, empleado_id, proyecto_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                registro.fecha,
                registro.horas_trabajadas,
                registro.descripcion,
                registro.empleado.id,
                registro.proyecto.id,
            ),
        )
        registro.id = cursor.lastrowid

    return registro.id

def buscar_por_id(id_registro: int) -> RegistroTiempo | None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM registros_tiempo WHERE id = %s", (id_registro,))
        fila = cursor.fetchone()
    return _fila_a_registro(fila) if fila else None

def listar_todos() -> list[RegistroTiempo]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM registros_tiempo")
        filas = cursor.fetchall()
    return [_fila_a_registro(fila) for fila in filas] if filas else []

def actualizar(registro: RegistroTiempo) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            """
            UPDATE registros_tiempo
            SET fecha = %s, horas_trabajadas = %s, descripcion = %s, proyecto_id = %s
            WHERE id = %s
            """,
            (
                registro.fecha,
                registro.horas_trabajadas,
                registro.descripcion,
                registro.proyecto.id,
                registro.id,
            ),
        )


def cargar_historial(empleado) -> None:
    """Puebla empleado._registros_tiempo con lo ya persistido."""

    empleado._limpiar_registros_tiempo()

    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            "SELECT * FROM registros_tiempo WHERE empleado_id = %s",
            (empleado.id,)
        )
        filas = cursor.fetchall()

    for fila in filas:
        proyecto = proyecto_repo.buscar_por_id(fila["proyecto_id"])
        registro = RegistroTiempo(
            fecha=fila["fecha"],
            horas_trabajadas=float(fila["horas_trabajadas"]),
            descripcion=fila["descripcion"],
            empleado=empleado,
            proyecto=proyecto,
        )
        registro.id = fila["id"]
        empleado._agregar_registro_tiempo(registro)

def listar_por_proyecto(proyecto_id: int) -> list[RegistroTiempo]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            """
            SELECT * FROM registros_tiempo 
            WHERE proyecto_id = %s
            """,
            (proyecto_id,),
        )
        filas = cursor.fetchall()
    return [_fila_a_registro(fila) for fila in filas]

def listar_por_empleado(empleado_id: int) -> list[RegistroTiempo]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            """
            SELECT * FROM registros_tiempo 
            WHERE empleado_id = %s
            """,
            (empleado_id,),
        )
        filas = cursor.fetchall()
    return [_fila_a_registro(fila) for fila in filas]

def eliminar(id_registro: int) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute("DELETE FROM registros_tiempo WHERE id = %s", (id_registro,))