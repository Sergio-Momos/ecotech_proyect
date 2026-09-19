import unicodedata



from utils.constantes import (
    PATRON_USERNAME, ERROR_USERNAME, 
    PATRON_PASSWORD, ERROR_PASSWORD
)
from utils.validaciones import validar_con_patron, validar_password, validar_id

from .seguridad import Seguridad
from .rol import Rol
class Usuario:
    def __init__(self, id: int, username: str, password: str):
        self._validar_id(id)
        self._id = id
        self.username = username
        self.password = password
        self.rol = rol
    @staticmethod
    def _validar_id(valor: int) -> None:
        validar_id(valor, "El id")

    @property
    def id(self) -> int:
        """Identificador inmutable del Usuario."""
        return self._id

    # --- GETTER Y SETTER DE USERNAME ---
    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, valor: str) -> None:
        # Usamos tu función para validar con el nuevo patrón de Regex
        self._username = validar_con_patron(
            valor, "El username", PATRON_USERNAME, ERROR_USERNAME
        )

    # --- GETTER Y SETTER DE PASSWORD ---
    @property
    def password(self) -> str:
        # Bloquea cualquier intento de hacer: print(usuario.password)
        raise AttributeError("Por seguridad, la contraseña no puede ser leída.")

    @password.setter
    def password(self, valor: str) -> None:
        valor_validado = validar_password(valor, PATRON_PASSWORD, ERROR_PASSWORD)
        self._password = Seguridad.hashear_password(valor_validado)
        
    def __str__(self) -> str:
        return f"Usuario: {self.username} (ID: {self.id})"

    @property
    def rol (self) -> Rol:
        return self._rol

    @rol.setter
    def rol(self, valor: Rol) -> None:
        if not isinstance(valor, Rol):
            raise TypeError("El rol debe ser una instancia de la clase Rol.")
        self._rol = valor


    # --- generación de username (pieza nueva) ---
    @staticmethod
    def _quitar_acentos(texto: str) -> str:
        forma = unicodedata.normalize("NFKD", texto)
        return "".join(c for c in forma if not unicodedata.combining(c))

    @classmethod
    def generar_username(cls, nombre_completo: str) -> str:
        partes = cls._quitar_acentos(nombre_completo).strip().split()
        if len(partes) < 2:
            raise ValueError("Se necesita nombre y apellido para generar el username.")

        inicial = partes[0][0].lower()
        apellido = partes[-1].lower()
        base = f"{inicial}.{apellido}"[: cls._LARGO_MAXIMO_USERNAME]

        candidato = base
        sufijo = 1
        while candidato in cls._usernames_registrados:
            sufijo += 1
            recorte = cls._LARGO_MAXIMO_USERNAME - len(str(sufijo))
            candidato = f"{base[:recorte]}{sufijo}"

        cls._usernames_registrados.add(candidato)
        return candidato

    def __str__(self) -> str:
        return f"Usuario: {self.username} (ID: {self.id})"