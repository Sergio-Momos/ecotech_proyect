from database.conexion import cursor_db
from models.departamento import Departamento
from repositorios import empleado_repo


def _fila_a_departamento(fila: dict) -> Departamento:
    gerente = empleado_repo.buscar_por_id(fila["gerente_id"])
    departamento = Departamento(id=fila["id"], nombre=fila["nombre"], gerente=gerente)

    for empleado in empleado_repo.listar_por_departamento(fila["id"]):
        departamento.agregar_empleado(empleado)  # reutiliza la validación del modelo

    return departamento


def crear(departamento: Departamento) -> int:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "INSERT INTO departamentos (nombre, gerente_id) VALUES (%s, %s)",
            (departamento._nombre, departamento._gerente._id),
        )
        departamento._id = cursor.lastrowid

    return departamento._id


def buscar_por_id(id_departamento: int) -> Departamento | None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM departamentos WHERE id = %s", (id_departamento,))
        fila = cursor.fetchone()
    return _fila_a_departamento(fila) if fila else None

def listar_todos() -> list[Departamento]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM departamentos")
        filas = cursor.fetchall()
    return [_fila_a_departamento(fila) for fila in filas]

def actualizar(departamento: Departamento) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE departamentos SET nombre = %s, gerente_id = %s WHERE id = %s",
            (
                departamento._nombre,
                departamento._gerente._id,
                departamento._id,
            ),
        )

def eliminar(id_departamento: int) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute("DELETE FROM departamentos WHERE id = %s", (id_departamento,))

def asignar_empleado(departamento_id: int, empleado_id: int) -> None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT id FROM departamentos WHERE id = %s FOR UPDATE", (departamento_id,))
        if cursor.fetchone() is None:
            raise ValueError("El departamento no existe.")
        cursor.execute(
            "SELECT id, departamento_id, activo FROM empleados WHERE id = %s FOR UPDATE",
            (empleado_id,),
        )
        empleado = cursor.fetchone()
        if empleado is None:
            raise ValueError("El empleado no existe.")
        if not empleado["activo"]:
            raise ValueError("No se puede asignar un empleado inactivo.")
        departamento_actual = empleado["departamento_id"]
        if departamento_actual == departamento_id:
            return
        if departamento_actual is not None:
            raise ValueError("El empleado ya pertenece a otro departamento.")
        cursor.execute(
            "UPDATE empleados SET departamento_id = %s WHERE id = %s AND departamento_id IS NULL",
            (departamento_id, empleado_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("El empleado fue asignado a otro departamento. Recargue la nómina.")

def quitar_empleado(empleado_id: int) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE empleados SET departamento_id = NULL WHERE id = %s", (empleado_id,)
        )
