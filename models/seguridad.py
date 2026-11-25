import secrets
import hashlib
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


class Seguridad:
    """Hash de contraseñas con Argon2id y hash determinístico para búsquedas."""

    _PASSWORD_HASHER = PasswordHasher()

    @staticmethod
    def hashear_password(password: str) -> str:
        """Genera un hash Argon2id en formato PHC."""
        return Seguridad._PASSWORD_HASHER.hash(password)

    @staticmethod
    def verificar_password(password: str, hash_guardado: str) -> bool:
        """Verifica hashes Argon2id nuevos y PBKDF2 heredados."""
        if hash_guardado.startswith("$"):
            try:
                return Seguridad._PASSWORD_HASHER.verify(hash_guardado, password)
            except (VerifyMismatchError, VerificationError, InvalidHashError):
                return False

        # Compatibilidad transitoria con el formato anterior: salt$PBKDF2-SHA256.
        try:
            salt, hash_esperado = hash_guardado.split("$", 1)
            hash_calculado = Seguridad._calcular_hash_legacy(password, salt)
        except (AttributeError, ValueError):
            return False
        return secrets.compare_digest(hash_calculado, hash_esperado)

    @staticmethod
    def necesita_rehash(hash_guardado: str) -> bool:
        """Indica si la credencial aún usa PBKDF2 o parámetros Argon2 antiguos."""
        if not hash_guardado.startswith("$"):
            return True
        try:
            return Seguridad._PASSWORD_HASHER.check_needs_rehash(hash_guardado)
        except (VerificationError, InvalidHashError):
            return True

    @staticmethod
    def _calcular_hash_legacy(password: str, salt: str) -> str:
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
        )
        return hash_bytes.hex()

    @staticmethod
    def hash_busqueda(dato: str) -> str:
        """Hash determinístico usado para comparar datos cifrados sin descifrarlos."""
        return hashlib.sha256(dato.encode("utf-8")).hexdigest()
