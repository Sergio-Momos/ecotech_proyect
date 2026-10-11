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
        self._valor_id = None  # lo asigna la base de datos al guardarlo
        self._valor_empleado = empleado  # sin setter — un registro nunca cambia de dueño
        self._fecha = fecha
        self._horas_trabajadas = horas_trabajadas
        self._descripcion = descripcion
        self._proyecto = proyecto

    @property
    def _id(self):
        return self._valor_id

    @_id.setter
    def _id(self, valor: int) -> None:
        if self._valor_id is not None:
            raise AttributeError("El id ya fue asignado y no puede modificarse.")
        if not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0:
            raise ValueError("El id debe ser un número entero mayor que cero.")
        self._valor_id = valor

    @property
    def _fecha(self) -> date:
        return self._valor_fecha

    @_fecha.setter
    def _fecha(self, valor: date) -> None:
        if not isinstance(valor, date):
            raise TypeError("La fecha debe ser una instancia de date")
        if valor > date.today():
            raise ValueError("La fecha no puede ser futura")
        self._valor_fecha = valor

    @property
    def _horas_trabajadas(self) -> float:
        return self._valor_horas_trabajadas

    @_horas_trabajadas.setter
    def _horas_trabajadas(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("Las horas trabajadas deben ser un número (int o float)")
        if valor <= 0:
            raise ValueError("Las horas trabajadas deben ser mayores que 0")
        if valor > 10:
            raise ValueError("Un solo registro no puede superar las 10 horas diarias permitidas por ley")
        self._valor_horas_trabajadas = float(valor)

    @property
    def _descripcion(self) -> str:
        return self._valor_descripcion

    @_descripcion.setter
    def _descripcion(self, valor: str) -> None:
        self._valor_descripcion = validar_texto(valor, "La descripción")

    @property
    def _empleado(self) -> "Empleado":
        return self._valor_empleado

    @property
    def _proyecto(self) -> "Proyecto":
        return self._valor_proyecto

    @_proyecto.setter
    def _proyecto(self, valor: "Proyecto") -> None:
        self._valor_proyecto = valor