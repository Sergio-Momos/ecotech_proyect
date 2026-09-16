from datetime import date

from .persona import Persona


class Empleado(Persona):
    """Persona contratada por EcoTech.

    Las relaciones con proyectos, departamentos y registros de tiempo se
    agregarán posteriormente, cuando se modele esa parte del diagrama.
    """

    def __init__(
        self,
        id: int,
        nombre: str,
        direccion: str,
        telefono: str,
        correo: str,
        rut: str,
        salario: float,
        fecha_inicio_contrato: date,
    ) -> None:
        super().__init__(id, nombre, direccion, telefono, correo, rut)
        self.salario = salario
        self.fecha_inicio_contrato = fecha_inicio_contrato

    @property
    def salario(self) -> float:
        return self._salario

    @salario.setter
    def salario(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("El salario debe ser un número (int o float)")
        if valor < 0:
            raise ValueError("El salario no puede ser menor que 0")
        self._salario = float(valor)


    @property
    def fecha_inicio_contrato(self) -> date:
        return self._fecha_inicio_contrato



    @fecha_inicio_contrato.setter
    def fecha_inicio_contrato(self, valor: date) -> None:
        if not isinstance(valor, date):
            raise TypeError("La fecha de inicio debe ser una instancia de date")
        self._fecha_inicio_contrato = valor
