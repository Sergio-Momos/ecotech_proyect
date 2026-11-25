from database.conexion import cursor_db
from models.departamento import Departamento
from repositorios import empleado_repo


def _fila_a_departamento(fila: dict) -> Departamento:
    """Reconstruye el departamento, su gerente y sus empleados asociados."""
    gerente = empleado_repo.buscar_por_id(fila["gerente_id"])
    departamento = Departamento(id=fila["id"], nombre=fila["nombre"], gerente=gerente)

    for empleado in empleado_repo.listar_por_departamento(fila["id"]):
        departamento.agregar_empleado(empleado)  # reutiliza la validación del modelo

    return departamento


def crear(departamento: Departamento) -> int:
    """Inserta el departamento y asigna al objeto el id generado por MySQL."""
    with cursor_db() as (cursor, _):
        cursor.execute(
            "INSERT INTO departamentos (nombre, gerente_id) VALUES (%s, %s)",
            (departamento._nombre, departamento._gerente._id),
        )
        departamento._id = cursor.lastrowid

    return departamento._id


def buscar_por_id(id_departamento: int) -> Departamento | None:
    """Busca un departamento por id y carga sus relaciones."""
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM departamentos WHERE id = %s", (id_departamento,))
        fila = cursor.fetchone()
    return _fila_a_departamento(fila) if fila else None

def listar_todos() -> list[Departamento]:
    """Devuelve todos los departamentos con sus gerentes y empleados."""
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM departamentos")
        filas = cursor.fetchall()
    return [_fila_a_departamento(fila) for fila in filas]

def actualizar(departamento: Departamento) -> None:
    """Guarda los cambios de nombre y gerente del departamento."""
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
    """Elimina físicamente el departamento indicado."""
    with cursor_db() as (cursor, _):
        cursor.execute("DELETE FROM departamentos WHERE id = %s", (id_departamento,))

def asignar_empleado(departamento_id: int, empleado_id: int) -> None:
    """Asocia un empleado al departamento actualizando su departamento_id."""
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE empleados SET departamento_id = %s WHERE id = %s",
            (departamento_id, empleado_id),
        )

def quitar_empleado(empleado_id: int) -> None:
    """Desasocia al empleado dejando departamento_id en NULL."""
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE empleados SET departamento_id = NULL WHERE id = %s", (empleado_id,)
        )
