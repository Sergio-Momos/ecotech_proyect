import hashlib
import hmac

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from config import AES_KEY


class Seguridad:
    """Hash de contraseñas con Argon2id y hash determinista de búsqueda."""

    _PASSWORD_HASHER = PasswordHasher()
    _ITERACIONES_PBKDF2 = 100_000

    @staticmethod
    def hashear_password(password: str) -> str:
        return Seguridad._PASSWORD_HASHER.hash(password)

    @staticmethod
    def verificar_password(password: str, hash_guardado: str) -> bool:
        if hash_guardado.startswith("$argon2"):
            try:
                return Seguridad._PASSWORD_HASHER.verify(hash_guardado, password)
            except (InvalidHashError, VerificationError, VerifyMismatchError):
                return False

        # Compatibility for hashes created by the previous PBKDF2 format: salt$hex_digest.
        try:
            salt, hash_esperado = hash_guardado.split("$", 1)
        except (AttributeError, ValueError):
            return False
        hash_calculado = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"),
            Seguridad._ITERACIONES_PBKDF2,
        ).hex()
        return hmac.compare_digest(hash_calculado, hash_esperado)

    @staticmethod
    def necesita_rehash(hash_guardado: str) -> bool:
        """Marca hashes heredados para migrarlos y Argon2 cuando sus parámetros cambian."""
        if not isinstance(hash_guardado, str) or not hash_guardado.startswith("$argon2"):
            return True
        try:
            return Seguridad._PASSWORD_HASHER.check_needs_rehash(hash_guardado)
        except (InvalidHashError, VerificationError):
            return False

    @staticmethod
    def hash_busqueda(dato: str) -> str:
        """HMAC estable para búsquedas y restricciones de unicidad."""
        if not AES_KEY:
            raise RuntimeError("Falta configurar FERNET_KEY en el archivo .env.")
        return hmac.new(
            AES_KEY.encode("utf-8"), dato.encode("utf-8"), "sha256"
        ).hexdigest()
