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
        self._id = None
        if id is not None:
            self.id = id  # pasa por el setter, con su validación
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.correo = correo
        self.rut = rut

    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        if self._id is not None:
            raise AttributeError("El id ya fue asignado y no puede modificarse.")
        validar_id(valor, "El id")
        self._id = valor

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = validar_con_patron(
            valor, "El nombre", PATRON_NOMBRE, ERROR_SOLO_LETRAS
        )

    @property
    def direccion(self) -> str:
        return self._direccion

    @direccion.setter
    def direccion(self, valor: str) -> None:
        self._direccion = validar_texto(valor, "La dirección")

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        self._telefono = validar_con_patron(
            valor, "El teléfono", PATRON_TELEFONO, ERROR_TELEFONO
        )

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        self._correo = validar_con_patron(valor, "El correo", PATRON_CORREO, ERROR_CORREO)

    @property
    def rut(self) -> str:
        return self._rut

    @rut.setter
    def rut(self, valor: str) -> None:
        valor = normalizar_rut(valor)
        if not validar_rut_chileno(valor):
            raise ValueError(ERROR_RUT)
        self._rut = valor

    def get_nombre_completo(self) -> str:
        """Devuelve el nombre tal como fue definido en el modelo."""
        return self.nombre

    def __str__(self) -> str:
        return f"{self.get_nombre_completo()} (RUT: {self.rut})"