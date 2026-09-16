class Persona:
    """Datos personales comunes a las personas registradas en EcoTech.

    Es la clase base de ``Empleado``. No conoce aún relaciones con
    departamentos, proyectos ni usuarios: esas responsabilidades pertenecen
    a las clases que las modelan.
    """

    def __init__(
        self,
        id: int,
        nombre: str,
        direccion: str,
        telefono: str,
        correo: str,
        rut: str,
    ) -> None:
        self._validar_id(id)
        self._id = id
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.correo = correo
        self.rut = rut

    @staticmethod
    def _validar_texto(valor: str, campo: str) -> str:
        if not isinstance(valor, str):
            raise TypeError(f"{campo} debe ser un texto.")

        valor = valor.strip()
        if not valor:
            raise ValueError(f"{campo} no puede estar vacío.")
        return valor

    @staticmethod
    def _validar_id(valor: int) -> None:
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise TypeError("El id debe ser un número entero.")
        if valor <= 0:
            raise ValueError("El id debe ser mayor que cero.")

    @property
    def id(self) -> int:
        """Identificador inmutable de la persona."""
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = self._validar_texto(valor, "El nombre")

    @property
    def direccion(self) -> str:
        return self._direccion

    @direccion.setter
    def direccion(self, valor: str) -> None:
        self._direccion = self._validar_texto(valor, "La dirección")

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        self._telefono = self._validar_texto(valor, "El teléfono")

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        correo = self._validar_texto(valor, "El correo")
        if correo.count("@") != 1:
            raise ValueError(f"Correo inválido: {valor}")

        usuario, dominio = correo.split("@")
        if not usuario or not dominio or "." not in dominio:
            raise ValueError(f"Correo inválido: {valor}")
        self._correo = correo

    @property
    def rut(self) -> str:
        return self._rut

    @rut.setter
    def rut(self, valor: str) -> None:
        self._rut = self._validar_texto(valor, "El RUT")

    def get_nombre_completo(self) -> str:
        """Devuelve el nombre tal como fue definido en el modelo."""
        return self.nombre

    def __str__(self) -> str:
        return f"{self.get_nombre_completo()} (RUT: {self.rut})"
