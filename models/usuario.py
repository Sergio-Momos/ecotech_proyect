import unicodedata

from .seguridad import Seguridad
from .rol import Rol
from utils.constantes import (
    PATRON_USERNAME, ERROR_USERNAME,
    PATRON_PASSWORD, ERROR_PASSWORD,
)
from utils.validaciones import validar_con_patron, validar_password, validar_id


class Usuario:
    _LARGO_MAXIMO_USERNAME = 20

    def __init__(self, id: int, username: str, password: str, rol: Rol, activo: bool= True) -> None:
        validar_id(id, "El id")
        self._valor_id = id
        self._username = username
        self._password = password
        self._rol = rol
        self._activo = activo
        

    # --- id ---
    @property
    def _id(self) -> int:
        return self._valor_id

    # --- username ---
    @property
    def _username(self) -> str:
        return self._valor_username

    @_username.setter
    def _username(self, valor: str) -> None:
        self._valor_username = validar_con_patron(
            valor, "El username", PATRON_USERNAME, ERROR_USERNAME
        )

    # --- password (escritura solamente, hasheada vía Seguridad) ---
    @property
    def _password(self) -> str:
        raise AttributeError("Por seguridad, la contraseña no puede ser leída.")

    @_password.setter
    def _password(self, valor: str) -> None:
        valor_validado = validar_password(valor, PATRON_PASSWORD, ERROR_PASSWORD)
        self._valor_password = Seguridad.hashear_password(valor_validado)

    # --- rol ---
    @property
    def _rol(self) -> Rol:
        return self._valor_rol

    @_rol.setter
    def _rol(self, valor: Rol) -> None:
        if not isinstance(valor, Rol):
            raise TypeError("El rol debe ser una instancia de la clase Rol.")
        self._valor_rol = valor

    # --- generación de username (pieza nueva) ---
    @staticmethod
    def _quitar_acentos(texto: str) -> str:
        forma = unicodedata.normalize("NFKD", texto)
        return "".join(c for c in forma if not unicodedata.combining(c))

    # usuario.py — agregar, junto a los demás métodos de instancia
    def verificar_password(self, password: str) -> bool:
        return Seguridad.verificar_password(password, self._valor_password)

    @classmethod
    def generar_base_username(cls, nombre_completo: str) -> str:
        partes = cls._quitar_acentos(nombre_completo).strip().split()
        if len(partes) < 2:
            raise ValueError("Se necesita nombre y apellido para generar el username.")
        inicial = partes[0][0].lower()
        apellido = partes[-1].lower()
        return f"{inicial}.{apellido}"[: cls._LARGO_MAXIMO_USERNAME]

    def __str__(self) -> str:
        return f"Usuario: {self._username} (ID: {self._id})"

    @classmethod
    def reconstruir(cls, id: int, username: str, password_hash: str, rol: Rol, activo: bool= True) -> "Usuario":
        """
        Reconstruye un Usuario ya existente a partir de un hash YA calculado
        (leído desde la BD). A diferencia de __init__, nunca tuvimos la
        contraseña original — solo su hash — así que no se puede pasar por
        el setter normal sin volver a hashearlo por error.
        """
        usuario = cls.__new__(cls)   # crea la instancia SIN llamar a __init__
        usuario._valor_id = id
        usuario._username = username        # sigue pasando por el setter (valida formato)
        usuario._valor_password = password_hash  # asignación directa — ya es un hash, no re-hashear
        usuario._rol = rol
        usuario._valor_activo = activo
        return usuario

    @property
    def _activo(self) -> bool:
        return self._valor_activo

    @_activo.setter
    def _activo(self, valor: bool) -> None:
        if not isinstance(valor, bool):
            raise TypeError("El estado activo debe ser un booleano.")
        self._valor_activo = valor

    def desactivar(self) -> None:
        self._activo = False

    def activar(self) -> None:
        self._activo = True
