import hashlib
import secrets
from contextlib import contextmanager

from database.conexion import cursor_db, establecer_perfil_activo, perfil_activo
from models.usuario import Usuario
from models.seguridad import Seguridad
from repositorios import rol_repo
from config import AES_KEY


@contextmanager
def _conexion_auth():
    perfil_anterior = perfil_activo()
    establecer_perfil_activo("auth")
    try:
        yield
    finally:
        establecer_perfil_activo(perfil_anterior)


def _fila_a_usuario(fila: dict) -> Usuario:
    """Convierte una fila SQL en Usuario y carga también su Rol relacionado."""
    rol = rol_repo.buscar_por_id(fila["rol_id"])
    return Usuario.reconstruir(
        id=fila["id"],
        username=fila["username"],
        password_hash=fila["password_hash"],
        rol=rol,
        activo=bool(fila["activo"]),
    )


def crear(usuario: Usuario) -> None:
    """Guarda la cuenta; reutiliza el id del empleado dueño como id de usuario."""
    # usuario.id YA existe de antes (reutiliza el id de su Empleado dueño)
    # — a diferencia de los demás crear(), no hay AUTO_INCREMENT que
    # sincronizar después.
    with cursor_db() as (cursor, _):
        cursor.execute(
            "INSERT INTO usuarios (id, username, password_hash, rol_id) VALUES (%s, %s, %s, %s)",
            (usuario._id, usuario._username, usuario._valor_password, usuario._rol._id),
        )


def buscar_por_username(username: str) -> Usuario | None:
    """Busca por username sin filtrar estado; devuelve None si no existe."""
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
        fila = cursor.fetchone()
    return _fila_a_usuario(fila) if fila else None

def buscar_por_id(id_usuario: int) -> Usuario | None:
    """Busca una cuenta por su id y la reconstruye como objeto Usuario."""
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id_usuario,))
        fila = cursor.fetchone()
    return _fila_a_usuario(fila) if fila else None

def listar_todos() -> list[Usuario]:
    """Devuelve todas las cuentas, activas o inactivas."""
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT * FROM usuarios")
        filas = cursor.fetchall()
    return [_fila_a_usuario(fila) for fila in filas]

def generar_username_unico(nombre_completo: str) -> str:
    """Genera inicial.apellido y añade un sufijo numérico si ya está ocupado."""
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
    username = generar_username_unico(empleado.get_nombre_completo())
    usuario = Usuario(id=empleado._id, username=username, password=password, rol=rol)
    crear(usuario)
    empleado._valor_usuario = usuario
    return usuario

def desactivar(id_usuario: int) -> None:
    """Deshabilita la cuenta sin borrarla, conservando su historial."""
    with cursor_db() as (cursor, _):
        cursor.execute("UPDATE usuarios SET activo = FALSE WHERE id = %s", (id_usuario,))

def cambiar_password(id_usuario: int, nueva_password: str) -> None:
    """Restablece la contraseña desde TI, validándola y guardando su hash Argon2."""
    from utils.validaciones import validar_password
    from utils.constantes import PATRON_PASSWORD, ERROR_PASSWORD
    from models.seguridad import Seguridad
    valor_validado = validar_password(nueva_password, PATRON_PASSWORD, ERROR_PASSWORD)
    nuevo_hash = Seguridad.hashear_password(valor_validado)
    with _conexion_auth():
        with cursor_db() as (cursor, _):
            cursor.execute(
                "UPDATE usuarios SET password_hash = %s, password_changed_at = NOW() WHERE id = %s",
                (nuevo_hash, id_usuario),
            )

def cambiar_password_propio(usuario: Usuario, password_actual: str, nueva_password: str) -> None:
    """Cambia la contraseña propia tras verificar la contraseña actual."""
    if not usuario.verificar_password(password_actual):
        raise ValueError("La contraseña actual es incorrecta.")
    cambiar_password(usuario._id, nueva_password)
    usuario._valor_password = Seguridad.hashear_password(nueva_password)


def password_vencida(id_usuario: int) -> bool:
    with _conexion_auth():
        with cursor_db() as (cursor, _):
            cursor.execute(
                "SELECT password_changed_at <= DATE_SUB(NOW(), INTERVAL 30 DAY) FROM usuarios WHERE id = %s",
                (id_usuario,),
            )
            fila = cursor.fetchone()
    return bool(fila and fila[0])

def buscar_por_username_activo(username: str) -> Usuario | None:
    """Solo devuelve el usuario si está activo — para el login."""
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            "SELECT * FROM usuarios WHERE username = %s AND activo = TRUE", (username,)
        )
        fila = cursor.fetchone()
    return _fila_a_usuario(fila) if fila else None

def actualizar_hash_password(usuario: Usuario, nuevo_hash: str) -> None:
    """Persiste el hash Argon2 generado tras verificar una contraseña heredada."""
    with cursor_db() as (cursor, _):
        cursor.execute(
            "UPDATE usuarios SET password_hash = %s WHERE id = %s",
            (nuevo_hash, usuario._id),
        )
    usuario._valor_password = nuevo_hash


def solicitar_recuperacion_password(nombre: str, rut: str, correo: str) -> tuple[str, str] | None:
    """Crea un código para una cuenta activa que coincide con nombre, RUT y correo."""
    from utils.validaciones import normalizar_rut

    nombre = nombre.strip()
    rut_normalizado = normalizar_rut(rut)
    correo = correo.strip()
    rut_hash = Seguridad.hash_busqueda(rut_normalizado)
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    token_hash = hashlib.sha256(codigo.encode("utf-8")).hexdigest()
    with _conexion_auth():
        with cursor_db(dictionary=True) as (cursor, _):
            cursor.execute(
                """SELECT u.id, CAST(AES_DECRYPT(e.correo, %s) AS CHAR) AS correo
                   FROM empleados e JOIN usuarios u ON u.id = e.id
                   WHERE u.activo = TRUE
                     AND e.rut_hash = %s
                     AND LOWER(TRIM(CONCAT_WS(' ', e.nombre, e.apellido))) = LOWER(TRIM(%s))
                     AND CAST(AES_DECRYPT(e.correo, %s) AS CHAR) = %s
                   LIMIT 1""",
                (AES_KEY, rut_hash, nombre, AES_KEY, correo),
            )
            fila = cursor.fetchone()
            if not fila:
                return None
            cursor.execute(
                "UPDATE password_reset_tokens SET used_at = NOW() WHERE empleado_id = %s AND used_at IS NULL",
                (fila["id"],),
            )
            cursor.execute(
                """INSERT INTO password_reset_tokens (empleado_id, token_hash, expires_at)
                   VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 10 MINUTE))""",
                (fila["id"], token_hash),
            )
    return fila["correo"], codigo


def recuperar_password(correo: str, codigo: str, nueva_password: str) -> None:
    """Valida el código vigente y cambia la contraseña en una transacción."""
    from utils.validaciones import validar_password
    from utils.constantes import PATRON_PASSWORD, ERROR_PASSWORD

    valor = validar_password(nueva_password, PATRON_PASSWORD, ERROR_PASSWORD)
    nuevo_hash = Seguridad.hashear_password(valor)
    token_hash = hashlib.sha256(codigo.strip().encode("utf-8")).hexdigest()
    with _conexion_auth():
        with cursor_db() as (cursor, _):
            cursor.execute(
                """SELECT t.id, t.empleado_id FROM password_reset_tokens t
                   JOIN empleados e ON e.id = t.empleado_id
                   JOIN usuarios u ON u.id = t.empleado_id
                   WHERE u.activo = TRUE AND t.used_at IS NULL AND t.expires_at > NOW()
                     AND t.token_hash = %s
                     AND CAST(AES_DECRYPT(e.correo, %s) AS CHAR) = %s
                   FOR UPDATE""",
                (token_hash, AES_KEY, correo.strip()),
            )
            token = cursor.fetchone()
            if token is None:
                raise ValueError("El código no es válido o ya venció.")
            cursor.execute(
                "UPDATE usuarios SET password_hash = %s, password_changed_at = NOW() WHERE id = %s",
                (nuevo_hash, token[1]),
            )
            cursor.execute(
                "UPDATE password_reset_tokens SET used_at = NOW() WHERE id = %s",
                (token[0],),
            )

def activar(id_usuario: int) -> None:
    """Vuelve a habilitar una cuenta previamente desactivada."""
    with cursor_db() as (cursor, _):
        cursor.execute("UPDATE usuarios SET activo = TRUE WHERE id = %s", (id_usuario,))
