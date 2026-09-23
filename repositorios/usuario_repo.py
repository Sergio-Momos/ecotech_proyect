from database.conexion import cursor_db
from models.usuario import Usuario
from repositorios import rol_repo


def _fila_a_usuario(fila: dict) -> Usuario:
    rol = rol_repo.buscar_por_id(fila["rol_id"])
    return Usuario.reconstruir(
        id=fila["id"], username=fila["username"],
        password_hash=fila["password_hash"], rol=rol,
    )


def crear(usuario: Usuario) -> None:
    # usuario.id YA existe de antes (reutiliza el id de su Empleado dueño)
    # — a diferencia de los demás crear(), no hay AUTO_INCREMENT que
    # sincronizar después.
    with cursor_db() as (cursor, _):
        cursor.execute(
            "INSERT INTO usuarios (id, username, password_hash, rol_id) VALUES (%s, %s, %s, %s)",
            (usuario.id, usuario.username, usuario._password, usuario.rol.id),
        )


def buscar_por_username(username: str) -> Usuario | None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
        fila = cursor.fetchone()
    return _fila_a_usuario(fila) if fila else None

def buscar_por_id(id_usuario: int) -> Usuario | None:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id_usuario,))
        fila = cursor.fetchone()
    return _fila_a_usuario(fila) if fila else None

def listar_todos() -> list[Usuario]:
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM usuarios")
        filas = cursor.fetchall()
    return [_fila_a_usuario(fila) for fila in filas] if filas else []

def generar_username_unico(nombre_completo: str) -> str:
    base = Usuario.generar_base_username(nombre_completo)
    candidato = base
    sufijo = 1
    while buscar_por_username(candidato) is not None:
        sufijo += 1
        recorte = Usuario._LARGO_MAXIMO_USERNAME - len(str(sufijo))
        candidato = f"{base[:recorte]}{sufijo}"
    return candidato

def crear_para_empleado(empleado, password: str, rol) -> Usuario:
    """Punto de entrada real para crear un Usuario persistido: genera un
    username garantizado único contra la BD (no contra memoria), y guarda
    de una vez. Esta es la función que debería usar la GUI — no
    Empleado.crear_usuario(), que solo resuelve colisiones en memoria."""
    username = generar_username_unico(empleado.nombre)
    usuario = Usuario(id=empleado.id, username=username, password=password, rol=rol)
    crear(usuario)
    empleado._usuario = usuario
    return usuario