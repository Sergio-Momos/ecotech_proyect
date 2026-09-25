from database.conexion import cursor_db
from models.empleado import Empleado
from models.seguridad import Seguridad


def _fila_a_empleado(fila: dict) -> Empleado:
    salario_centavos = int(Seguridad.descifrar_datos(fila["salario"]))
    return Empleado(
        id=fila["id"], 
        nombre=fila["nombre"],
        direccion=Seguridad.descifrar_datos(fila["direccion"]),
        telefono=Seguridad.descifrar_datos(fila["telefono"]),
        correo=Seguridad.descifrar_datos(fila["correo"]),
        rut=Seguridad.descifrar_datos(fila["rut"]),
        salario=salario_centavos / 100,
        fecha_inicio_contrato=fila["fecha_inicio_contrato"],
        activo=bool(fila["activo"]),
    )

def listar_por_departamento(departamento_id: int) -> list[Empleado]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            "SELECT * FROM empleados WHERE departamento_id = %s", (departamento_id,)
        )
        filas = cursor.fetchall()
    return [_fila_a_empleado(fila) for fila in filas]


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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                empleado.nombre,
                Seguridad.cifrar_datos(empleado.direccion),
                Seguridad.cifrar_datos(empleado.telefono),
                Seguridad.cifrar_datos(empleado.correo),
                Seguridad.cifrar_datos(empleado.rut),
                rut_hash,
                Seguridad.cifrar_datos(str(salario_centavos)),
                empleado.fecha_inicio_contrato,
            ),
        )
        empleado.id = cursor.lastrowid   # ← sincroniza el objeto en memoria

    return empleado.id


def buscar_por_id(id_empleado: int) -> Empleado | None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM empleados WHERE id = %s", (id_empleado,))
        fila = cursor.fetchone()
    return _fila_a_empleado(fila) if fila else None


def listar_todos(incluir_inactivos: bool = False) -> list[Empleado]:
    with cursor_db(dictionary=True) as (cursor, _):
        if incluir_inactivos:
            cursor.execute("""
                SELECT e.* FROM empleados e
                WHERE e.id NOT IN (
                    SELECT u.id FROM usuarios u
                    JOIN roles r ON u.rol_id = r.id
                    WHERE r.perfil_bd = 'ti'
                )
            """)
        else:
            cursor.execute("""
                SELECT e.* FROM empleados e
                WHERE e.activo = TRUE
                AND e.id NOT IN (
                    SELECT u.id FROM usuarios u
                    JOIN roles r ON u.rol_id = r.id
                    WHERE u.activo = TRUE AND r.perfil_bd = 'ti'
                )
            """)
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
            SET nombre = %s, direccion = %s, telefono = %s, correo = %s,
                rut = %s, rut_hash = %s, salario = %s, fecha_inicio_contrato = %s
            WHERE id = %s
            """,
            (
                empleado.nombre,
                Seguridad.cifrar_datos(empleado.direccion),
                Seguridad.cifrar_datos(empleado.telefono),
                Seguridad.cifrar_datos(empleado.correo),
                Seguridad.cifrar_datos(empleado.rut),
                rut_hash,
                Seguridad.cifrar_datos(str(salario_centavos)),
                empleado.fecha_inicio_contrato,
                empleado.id,
            ),
        )

def eliminar(id_empleado: int) -> None:
    # Borrado lógico — preserva el historial de RegistroTiempo, que de
    # otro modo se perdería por el ON DELETE CASCADE del esquema.
    with cursor_db() as (cursor, _):
        cursor.execute("UPDATE empleados SET activo = FALSE WHERE id = %s", (id_empleado,))

def listar_por_proyecto(proyecto_id: int) -> list[Empleado]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            """
            SELECT e.* FROM empleados e
            JOIN empleados_proyectos ep ON e.id = ep.empleado_id
            WHERE ep.proyecto_id = %s
            """,
            (proyecto_id,),
        )
        filas = cursor.fetchall()
    return [_fila_a_empleado(fila) for fila in filas]