from database.conexion import cursor_db
from repositorios import empleado_repo, proyecto_repo
from models.registro_tiempo import RegistroTiempo
from datetime import date


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
    registro._id = fila["id"]
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
                registro._fecha,
                registro._horas_trabajadas,
                registro._descripcion,
                registro._empleado._id,
                registro._proyecto._id,
            ),
        )
        registro._id = cursor.lastrowid

    return registro._id

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

def listar(
    empleado_id: int | None = None,
    proyecto_id: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> list[RegistroTiempo]:

    condiciones = []
    parametros = []

    if empleado_id is not None:
        condiciones.append("empleado_id = %s")
        parametros.append(empleado_id)
    if proyecto_id is not None:
        condiciones.append("proyecto_id = %s")
        parametros.append(proyecto_id)
    if desde is not None:
        condiciones.append("fecha >= %s")
        parametros.append(desde)
    if hasta is not None:
        condiciones.append("fecha <= %s")
        parametros.append(hasta)

    sql = "SELECT * FROM registros_tiempo"
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " ORDER BY fecha DESC, id DESC"

    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(sql, tuple(parametros))
        filas = cursor.fetchall()
    return [_fila_a_registro(fila) for fila in filas]

def actualizar(registro: RegistroTiempo) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            """
            UPDATE registros_tiempo
            SET fecha = %s, horas_trabajadas = %s, descripcion = %s, proyecto_id = %s
            WHERE id = %s
            """,
            (
                registro._fecha,
                registro._horas_trabajadas,
                registro._descripcion,
                registro._proyecto._id,
                registro._id,
            ),
        )


def cargar_historial(empleado) -> None:
    """Puebla empleado._valor_registros_tiempo con lo ya persistido."""

    empleado._limpiar_registros_tiempo()

    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            "SELECT * FROM registros_tiempo WHERE empleado_id = %s",
            (empleado._id,)
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
        registro._id = fila["id"]
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
