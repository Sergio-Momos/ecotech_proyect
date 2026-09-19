from datetime import date
from typing import TYPE_CHECKING
from utils.validaciones import validar_texto

if TYPE_CHECKING:
    from .empleado import Empleado
    from .proyecto import Proyecto

class RegistroTiempo:
    def __init__(
        self,
        fecha: date,
        horas_trabajadas: float,
        descripcion: str,
        empleado: "Empleado",
        proyecto: "Proyecto",
    ) -> None:
        self._id = None  # lo asigna la base de datos al guardarlo
        self._empleado = empleado  # sin setter — un registro nunca cambia de dueño
        self.fecha = fecha
        self.horas_trabajadas = horas_trabajadas
        self.descripcion = descripcion
        self.proyecto = proyecto

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        if self._id is not None:
            raise AttributeError("El id ya fue asignado y no puede modificarse.")
        if not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0:
            raise ValueError("El id debe ser un número entero mayor que cero.")
        self._id = valor

    @property
    def fecha(self) -> date:
        return self._fecha

    @fecha.setter
    def fecha(self, valor: date) -> None:
        if not isinstance(valor, date):
            raise TypeError("La fecha debe ser una instancia de date")
        if valor > date.today():
            raise ValueError("La fecha no puede ser futura")
        self._fecha = valor

    @property
    def horas_trabajadas(self) -> float:
        return self._horas_trabajadas

    @horas_trabajadas.setter
    def horas_trabajadas(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("Las horas trabajadas deben ser un número (int o float)")
        if valor <= 0:
            raise ValueError("Las horas trabajadas deben ser mayores que 0")
        if valor > 10:
            raise ValueError("Un solo registro no puede superar las 10 horas diarias permitidas por ley")
        self._horas_trabajadas = float(valor)

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor: str) -> None:
        self._descripcion = validar_texto(valor, "La descripción")

    @property
    def empleado(self) -> "Empleado":
        return self._empleado

    @property
    def proyecto(self) -> "Proyecto":
        return self._proyecto

    @proyecto.setter
    def proyecto(self, valor: "Proyecto") -> None:
        self._proyecto = valor