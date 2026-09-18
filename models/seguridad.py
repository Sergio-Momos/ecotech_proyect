import hashlib
import secrets

class Seguridad:
    """Utilidades de seguridad: hash de contraseñas.
    Cifrado de datos sensibles (cifrar_datos/descifrar_datos): pendiente,
    decisión de equipo — ver notas del proyecto.
    """

    _ITERACIONES = 100_000
    _LARGO_SALT = 16  # bytes

    @staticmethod
    def hashear_password(password: str) -> str:
        salt = secrets.token_hex(Seguridad._LARGO_SALT)
        hash_hex = Seguridad._calcular_hash(password, salt)
        return f"{salt}${hash_hex}"

    @staticmethod
    def verificar_password(password: str, hash_guardado: str) -> bool:
        try:
            salt, hash_esperado = hash_guardado.split("$", 1)
        except ValueError:
            raise ValueError("Formato de hash inválido.")
        hash_calculado = Seguridad._calcular_hash(password, salt)
        return secrets.compare_digest(hash_calculado, hash_esperado)

    @staticmethod
    def _calcular_hash(password: str, salt: str) -> str:
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            Seguridad._ITERACIONES,
        )
        return hash_bytes.hex()