from database.conexion import cursor_db
from repositorios import empleado_repo, proyecto_repo
from models.registro_tiempo import RegistroTiempo
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
    registro.id = fila["id"]
    return registro


def _validar_usuario(usuario) -> None:
    if usuario is None or not usuario.activo:
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
    validar_id(registro.proyecto.id, "El id del proyecto")
    cursor.execute(
        "SELECT id FROM proyectos WHERE id = %s AND (activo = TRUE OR id = %s)",
        (registro.proyecto.id, proyecto_anterior),
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
            registro.fecha,
            registro.horas_trabajadas,
            registro.descripcion,
            registro.empleado.id,
            registro.proyecto.id,
        ),
    )
    return cursor.lastrowid


def crear(registro: RegistroTiempo, *, usuario) -> int:
    return crear_lote([registro], usuario=usuario)[0]


def crear_lote(registros: list[RegistroTiempo], *, usuario) -> list[int]:
    """Valida el historial persistido y confirma todo el lote en una transacción."""
    _validar_usuario(usuario)
    if not usuario.rol.tiene_permiso(Rol.CREAR_REGISTRO_PROPIO):
        raise PermissionError("No tienes permiso para registrar horas.")
    for registro in registros:
        if registro.empleado.id != usuario.id:
            raise PermissionError("Solo puedes registrar tus propias horas.")
        if registro.id is not None:
            raise ValueError("El registro ya tiene un id asignado.")
    if not registros:
        return []
    ids = []
    with cursor_db(dictionary=True) as (cursor, _):
        _bloquear_empleados(cursor, usuario.id, usuario.id)
        historial = _historial(cursor, usuario.id)
        for registro in registros:
            _validar_proyecto(cursor, registro)
            validar_historial_horas(
                registro.fecha, registro.horas_trabajadas,
                ((r["fecha"], r["horas_trabajadas"]) for r in historial),
            )
            ids.append(_insertar(cursor, registro))
            historial.append({"fecha": registro.fecha, "horas_trabajadas": registro.horas_trabajadas})
    # Los objetos solo reciben ids cuando el commit ya terminó correctamente.
    for registro, id_registro in zip(registros, ids):
        registro.id = id_registro
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
    return [_fila_a_registro(fila) for fila in filas] if filas else []

def actualizar(registro: RegistroTiempo, *, usuario) -> None:
    _validar_usuario(usuario)
    puede_editar_todos = usuario.rol.tiene_permiso(Rol.ACTUALIZAR_REGISTROS)
    puede_editar_propio = usuario.rol.tiene_permiso(Rol.ACTUALIZAR_REGISTRO_PROPIO)
    if not puede_editar_todos and not (puede_editar_propio and usuario.id == registro.empleado.id):
        raise PermissionError("No tienes permiso para editar este registro.")
    validar_id(registro.id, "El id del registro")
    with cursor_db(dictionary=True) as (cursor, _):
        _bloquear_empleados(cursor, usuario.id, registro.empleado.id)
        historial = _historial(cursor, registro.empleado.id)
        previo = next((r for r in historial if r["id"] == registro.id), None)
        if previo is None:
            raise ValueError("El registro ya no existe o pertenece a otro empleado.")
        _validar_proyecto(cursor, registro, previo["proyecto_id"])
        validar_historial_horas(
            registro.fecha, registro.horas_trabajadas,
            ((r["fecha"], r["horas_trabajadas"]) for r in historial if r["id"] != registro.id),
        )
        cursor.execute(
            """
            UPDATE registros_tiempo
            SET fecha = %s, horas_trabajadas = %s, descripcion = %s, proyecto_id = %s
            WHERE id = %s AND empleado_id = %s
            """,
            (
                registro.fecha,
                registro.horas_trabajadas,
                registro.descripcion,
                registro.proyecto.id,
                registro.id,
                registro.empleado.id,
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

def eliminar(id_registro: int, *, usuario) -> None:
    _validar_usuario(usuario)
    if not usuario.rol.tiene_permiso(Rol.ELIMINAR_REGISTROS):
        raise PermissionError("No tienes permiso para eliminar registros.")
    with cursor_db() as (cursor, _):
        cursor.execute("DELETE FROM registros_tiempo WHERE id = %s", (id_registro,))
