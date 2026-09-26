from database.conexion import cursor_db
from models.empleado import Empleado
from models.seguridad import Seguridad
from config import AES_KEY


def _fila_a_empleado(fila: dict) -> Empleado:
    salario_centavos = int(fila["salario"])
    return Empleado(
        id=fila["id"],
        nombre=fila["nombre"],
        direccion=fila["direccion"],
        telefono=fila["telefono"],
        correo=fila["correo"],
        rut=fila["rut"],
        salario=salario_centavos / 100,
        fecha_inicio_contrato=fila["fecha_inicio_contrato"],
        activo=bool(fila["activo"]),
    )


def _select_cifrado(where: str) -> str:
    """Construye el SELECT con AES_DECRYPT y CAST para todas las columnas cifradas."""
    return f"""
        SELECT id, nombre,
            CAST(AES_DECRYPT(direccion, %s) AS CHAR) AS direccion,
            CAST(AES_DECRYPT(telefono,  %s) AS CHAR) AS telefono,
            CAST(AES_DECRYPT(correo,    %s) AS CHAR) AS correo,
            CAST(AES_DECRYPT(rut,       %s) AS CHAR) AS rut,
            CAST(AES_DECRYPT(salario,   %s) AS CHAR) AS salario,
            rut_hash, fecha_inicio_contrato, activo, departamento_id
        FROM empleados
        {where}
    """


def crear(empleado: Empleado) -> int:
    rut_hash = Seguridad.hash_busqueda(empleado.rut)

    with cursor_db() as (cursor, _):
        cursor.execute("SELECT id FROM empleados WHERE rut_hash = %s", (rut_hash,))
        if cursor.fetchone() is not None:
            raise ValueError(f"Ya existe un empleado con el RUT {empleado.rut}.")

        salario_centavos = round(empleado.salario * 100)
        cursor.execute(
            """
            INSERT INTO empleados
                (nombre, direccion, telefono, correo, rut, rut_hash, salario, fecha_inicio_contrato)
            VALUES (%s,
                    AES_ENCRYPT(%s, %s), AES_ENCRYPT(%s, %s),
                    AES_ENCRYPT(%s, %s), AES_ENCRYPT(%s, %s),
                    %s, AES_ENCRYPT(%s, %s), %s)
            """,
            (
                empleado.nombre,
                empleado.direccion, AES_KEY,
                empleado.telefono,  AES_KEY,
                empleado.correo,    AES_KEY,
                empleado.rut,       AES_KEY,
                rut_hash,
                str(salario_centavos), AES_KEY,
                empleado.fecha_inicio_contrato,
            ),
        )
        empleado.id = cursor.lastrowid

    return empleado.id


def buscar_por_id(id_empleado: int) -> Empleado | None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            _select_cifrado("WHERE id = %s"),
            (AES_KEY, AES_KEY, AES_KEY, AES_KEY, AES_KEY, id_empleado),
        )
        fila = cursor.fetchone()
    return _fila_a_empleado(fila) if fila else None


def listar_todos(incluir_inactivos: bool = False) -> list[Empleado]:
    with cursor_db(dictionary=True) as (cursor, _):
        if incluir_inactivos:
            where = """
                WHERE id NOT IN (
                    SELECT u.id FROM usuarios u
                    JOIN roles r ON u.rol_id = r.id
                    WHERE r.perfil_bd = 'ti'
                )
            """
        else:
            where = """
                WHERE activo = TRUE
                AND id NOT IN (
                    SELECT u.id FROM usuarios u
                    JOIN roles r ON u.rol_id = r.id
                    WHERE u.activo = TRUE AND r.perfil_bd = 'ti'
                )
            """
        cursor.execute(
            _select_cifrado(where),
            (AES_KEY, AES_KEY, AES_KEY, AES_KEY, AES_KEY),
        )
        filas = cursor.fetchall()
    return [_fila_a_empleado(fila) for fila in filas]


def listar_por_departamento(departamento_id: int) -> list[Empleado]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            _select_cifrado("WHERE departamento_id = %s"),
            (AES_KEY, AES_KEY, AES_KEY, AES_KEY, AES_KEY, departamento_id),
        )
        filas = cursor.fetchall()
    return [_fila_a_empleado(fila) for fila in filas]


def listar_por_proyecto(proyecto_id: int) -> list[Empleado]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            _select_cifrado("""
                JOIN empleados_proyectos ep ON empleados.id = ep.empleado_id
                WHERE ep.proyecto_id = %s
            """),
            (AES_KEY, AES_KEY, AES_KEY, AES_KEY, AES_KEY, proyecto_id),
        )
        filas = cursor.fetchall()
    return [_fila_a_empleado(fila) for fila in filas]


def actualizar(empleado: Empleado) -> None:
    rut_hash = Seguridad.hash_busqueda(empleado.rut)

    with cursor_db() as (cursor, _):
        cursor.execute(
            "SELECT id FROM empleados WHERE rut_hash = %s AND id != %s",
            (rut_hash, empleado.id),
        )
        if cursor.fetchone() is not None:
            raise ValueError(f"Ya existe otro empleado con el RUT {empleado.rut}.")

        salario_centavos = round(empleado.salario * 100)
        cursor.execute(
            """
            UPDATE empleados
            SET nombre = %s,
                direccion = AES_ENCRYPT(%s, %s),
                telefono  = AES_ENCRYPT(%s, %s),
                correo    = AES_ENCRYPT(%s, %s),
                rut       = AES_ENCRYPT(%s, %s),
                rut_hash  = %s,
                salario   = AES_ENCRYPT(%s, %s),
                fecha_inicio_contrato = %s
            WHERE id = %s
            """,
            (
                empleado.nombre,
                empleado.direccion, AES_KEY,
                empleado.telefono,  AES_KEY,
                empleado.correo,    AES_KEY,
                empleado.rut,       AES_KEY,
                rut_hash,
                str(salario_centavos), AES_KEY,
                empleado.fecha_inicio_contrato,
                empleado.id,
            ),
        )


def eliminar(id_empleado: int) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE empleados SET activo = FALSE WHERE id = %s", (id_empleado,)
        )