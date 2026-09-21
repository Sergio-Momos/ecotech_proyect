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
            (departamento.nombre, departamento.gerente.id),
        )
        departamento.id = cursor.lastrowid

    return departamento.id


def buscar_por_id(id_departamento: int) -> Departamento | None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM departamentos WHERE id = %s", (id_departamento,))
        fila = cursor.fetchone()
    return _fila_a_departamento(fila) if fila else None

def listar_todos() -> list[Departamento]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM departamentos")
        filas = cursor.fetchall()
    return [_fila_a_departamento(fila) for fila in filas] if filas else []

def actualizar(departamento: Departamento) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE departamentos SET nombre = %s, gerente_id = %s WHERE id = %s",
            (
                departamento.nombre,
                departamento.gerente.id,
                departamento.id,
            ),
        )

def eliminar(id_departamento: int) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute("DELETE FROM departamentos WHERE id = %s", (id_departamento,))

def asignar_empleado(departamento_id: int, empleado_id: int) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE empleados SET departamento_id = %s WHERE id = %s",
            (departamento_id, empleado_id),
        )

def quitar_empleado(empleado_id: int) -> None:
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE empleados SET departamento_id = NULL WHERE id = %s", (empleado_id,)
        )