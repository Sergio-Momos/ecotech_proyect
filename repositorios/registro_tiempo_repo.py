from database.conexion import cursor_db, perfil_activo
from repositorios import empleado_repo, proyecto_repo
from models.registro_tiempo import RegistroTiempo
from datetime import date
from models.rol import Rol
from utils.validaciones import validar_historial_horas, validar_id


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


def _validar_usuario(usuario) -> None:
    if usuario is None or not usuario._activo:
        raise PermissionError("Se requiere un usuario activo.")


def _bloquear_empleados(cursor, usuario_id: int, empleado_id: int) -> None:
    # Todas las escrituras del historial toman estos bloqueos en el mismo orden.
    # El bloqueo del empleado serializa incluso dos inserciones en un día vacío.
    for id_empleado in sorted({usuario_id, empleado_id}):
        cursor.execute("SELECT id, activo FROM empleados WHERE id = %s FOR UPDATE", (id_empleado,))
        fila = cursor.fetchone()
        if fila is None:
            raise ValueError("El empleado no existe.")
        if id_empleado == usuario_id and not fila["activo"]:
            raise PermissionError("El empleado asociado a la sesión está inactivo.")


def _historial(cursor, empleado_id: int) -> list[dict]:
    cursor.execute(
        "SELECT id, fecha, horas_trabajadas, proyecto_id FROM registros_tiempo "
        "WHERE empleado_id = %s FOR UPDATE", (empleado_id,),
    )
    return list(cursor.fetchall())


def _validar_proyecto(cursor, registro, proyecto_anterior=None) -> None:
    validar_id(registro._proyecto._id, "El id del proyecto")
    cursor.execute(
        "SELECT id FROM proyectos WHERE id = %s AND (activo = TRUE OR id = %s)",
        (registro._proyecto._id, proyecto_anterior),
    )
    if cursor.fetchone() is None:
        raise ValueError("El proyecto seleccionado no existe o está inactivo.")


def _insertar(cursor, registro) -> int:
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
    return cursor.lastrowid


def crear(registro: RegistroTiempo, *, usuario=None) -> int:
    if perfil_activo() == "ti":
        raise PermissionError("El perfil TI no puede registrar horas.")
    return crear_lote([registro], usuario=usuario)[0]


def crear_lote(registros: list[RegistroTiempo], *, usuario) -> list[int]:
    """Valida el historial persistido y confirma todo el lote en una transacción."""
    _validar_usuario(usuario)
    if perfil_activo() == "ti" or not usuario._rol.tiene_permiso(Rol._CREAR_REGISTRO_PROPIO):
        raise PermissionError("No tienes permiso para registrar horas.")
    for registro in registros:
        if (date.today() - registro._fecha).days > 30:
            raise ValueError("Solo se pueden registrar horas de los últimos 30 días.")
        if registro._fecha < registro._empleado._fecha_inicio_contrato:
            raise ValueError("No se pueden registrar horas anteriores al inicio del contrato.")
        if registro._empleado._id != usuario._id:
            raise PermissionError("Solo puedes registrar tus propias horas.")
        if registro._id is not None:
            raise ValueError("El registro ya tiene un id asignado.")
    if not registros:
        return []
    ids = []
    with cursor_db(dictionary=True) as (cursor, _):
        _bloquear_empleados(cursor, usuario._id, usuario._id)
        historial = _historial(cursor, usuario._id)
        for registro in registros:
            _validar_proyecto(cursor, registro)
            validar_historial_horas(
                registro._fecha, registro._horas_trabajadas,
                ((r["fecha"], r["horas_trabajadas"]) for r in historial),
            )
            ids.append(_insertar(cursor, registro))
            historial.append({"fecha": registro._fecha, "horas_trabajadas": registro._horas_trabajadas})
    # Los objetos solo reciben ids cuando el commit ya terminó correctamente.
    for registro, id_registro in zip(registros, ids):
        registro._id = id_registro
    return ids

def buscar_por_id(id_registro: int) -> RegistroTiempo | None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM registros_tiempo WHERE id = %s", (id_registro,))
        fila = cursor.fetchone()
    return _fila_a_registro(fila) if fila else None

def listar_todos() -> list[RegistroTiempo]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM registros_tiempo")
        filas = cursor.fetchall()
    return [_fila_a_registro(fila) for fila in filas]

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

def actualizar(registro: RegistroTiempo, *, usuario) -> None:
    _validar_usuario(usuario)
    if usuario._rol._perfil_bd == "ti" or not usuario._rol.tiene_permiso(Rol._ACTUALIZAR_REGISTROS):
        raise PermissionError("No tienes permiso para editar este registro.")
    validar_id(registro._id, "El id del registro")
    with cursor_db(dictionary=True) as (cursor, _):
        _bloquear_empleados(cursor, usuario._id, registro._empleado._id)
        historial = _historial(cursor, registro._empleado._id)
        previo = next((r for r in historial if r["id"] == registro._id), None)
        if previo is None:
            raise ValueError("El registro ya no existe o pertenece a otro empleado.")
        _validar_proyecto(cursor, registro, previo["proyecto_id"])
        validar_historial_horas(
            registro._fecha, registro._horas_trabajadas,
            ((r["fecha"], r["horas_trabajadas"]) for r in historial if r["id"] != registro._id),
        )
        cursor.execute(
            """
            UPDATE registros_tiempo
            SET fecha = %s, horas_trabajadas = %s, descripcion = %s, proyecto_id = %s
            WHERE id = %s AND empleado_id = %s
            """,
            (
                registro._fecha,
                registro._horas_trabajadas,
                registro._descripcion,
                registro._proyecto._id,
                registro._id,
                registro._empleado._id,
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

def eliminar(id_registro: int, *, usuario) -> None:
    _validar_usuario(usuario)
    if not usuario._rol.tiene_permiso(Rol._ELIMINAR_REGISTROS):
        raise PermissionError("No tienes permiso para eliminar registros.")
    with cursor_db() as (cursor, _):
        cursor.execute("DELETE FROM registros_tiempo WHERE id = %s", (id_registro,))
