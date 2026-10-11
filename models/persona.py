from utils.constantes import (
    ERROR_CORREO,
    ERROR_RUT,
    ERROR_SOLO_LETRAS,
    ERROR_TELEFONO,
    PATRON_CORREO,
    PATRON_NOMBRE,
    PATRON_TELEFONO,
)
from utils.validaciones import (
    normalizar_rut,
    validar_con_patron,
    validar_rut_chileno,
    validar_texto,
    validar_id,
)


class Persona:

    def __init__(
        self,
        id: int | None,
        nombre: str,
        direccion: str,
        telefono: str,
        correo: str,
        rut: str,
    ) -> None:
        self._valor_id = None
        if id is not None:
            self._id = id  # pasa por el setter, con su validación
        self._nombre = nombre
        self._direccion = direccion
        self._telefono = telefono
        self._correo = correo
        self._rut = rut

    @property
    def _id(self) -> int | None:
        return self._valor_id

    @_id.setter
    def _id(self, valor: int) -> None:
        if self._valor_id is not None:
            raise AttributeError("El id ya fue asignado y no puede modificarse.")
        validar_id(valor, "El id")
        self._valor_id = valor

    @property
    def _nombre(self) -> str:
        return self._valor_nombre

    @_nombre.setter
    def _nombre(self, valor: str) -> None:
        self._valor_nombre = validar_con_patron(
            valor, "El nombre", PATRON_NOMBRE, ERROR_SOLO_LETRAS
        )

    @property
    def _direccion(self) -> str:
        return self._valor_direccion

    @_direccion.setter
    def _direccion(self, valor: str) -> None:
        self._valor_direccion = validar_texto(valor, "La dirección")

    @property
    def _telefono(self) -> str:
        return self._valor_telefono

    @_telefono.setter
    def _telefono(self, valor: str) -> None:
        self._valor_telefono = validar_con_patron(
            valor, "El teléfono", PATRON_TELEFONO, ERROR_TELEFONO
        )

    @property
    def _correo(self) -> str:
        return self._valor_correo

    @_correo.setter
    def _correo(self, valor: str) -> None:
        self._valor_correo = validar_con_patron(valor, "El correo", PATRON_CORREO, ERROR_CORREO)

    @property
    def _rut(self) -> str:
        return self._valor_rut

    @_rut.setter
    def _rut(self, valor: str) -> None:
        valor = normalizar_rut(valor)
        if not validar_rut_chileno(valor):
            raise ValueError(ERROR_RUT)
        self._valor_rut = valor

    def get_nombre_completo(self) -> str:
        """Devuelve el nombre tal como fue definido en el modelo."""
        return self._nombre

    def __str__(self) -> str:
        return f"{self.get_nombre_completo()} (RUT: {self._rut})"