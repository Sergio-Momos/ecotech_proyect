from utils.constantes import (
    PATRON_USERNAME, ERROR_USERNAME, 
    PATRON_PASSWORD, ERROR_PASSWORD
)
from utils.validaciones import validar_con_patron, validar_password

class Usuario:
    def __init__(self, id: int, username: str, password: str):
        self._validar_id(id)
        self._id = id
        self.username = username
        self.password = password

    @staticmethod
    def _validar_id(valor: int) -> None:
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise TypeError("El id debe ser un número entero.")
        if valor <= 0:
            raise ValueError("El id debe ser mayor que cero.")

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
        self._password = validar_password(valor, PATRON_PASSWORD, ERROR_PASSWORD)
        
    def __str__(self) -> str:
        return f"Usuario: {self.username} (ID: {self.id})"
