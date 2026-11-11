import hmac

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from config import AES_KEY


class Seguridad:
    """Hash de contraseñas con Argon2id y hash determinista de búsqueda."""

    _PASSWORD_HASHER = PasswordHasher()

    @staticmethod
    def hashear_password(password: str) -> str:
        return Seguridad._PASSWORD_HASHER.hash(password)

    @staticmethod
    def verificar_password(password: str, hash_guardado: str) -> bool:
        if not hash_guardado.startswith("$argon2"):
            return False
        try:
            return Seguridad._PASSWORD_HASHER.verify(hash_guardado, password)
        except (InvalidHashError, VerificationError, VerifyMismatchError):
            return False

    @staticmethod
    def hash_busqueda(dato: str) -> str:
        """HMAC estable para búsquedas y restricciones de unicidad."""
        if not AES_KEY:
            raise RuntimeError("Falta configurar FERNET_KEY en el archivo .env.")
        return hmac.new(
            AES_KEY.encode("utf-8"), dato.encode("utf-8"), "sha256"
        ).hexdigest()
