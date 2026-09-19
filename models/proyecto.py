from .empleado import Empleado
from utils.validaciones import validar_id, validar_con_patron, validar_texto
from utils.constantes import PATRON_NOMBRE, ERROR_SOLO_LETRAS
from datetime import date


class Proyecto:
    def __init__(self, id: int, nombre: str, descripcion: str, fecha_inicio: date):
        self._validar_id(id)
        self._id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.fecha_inicio = fecha_inicio
        self._empleados = []

    @staticmethod
    def _validar_id(valor: int) -> None:
        validar_id(valor, "El id")
    
    @property
    def id(self) -> int:
        return self._id
    
    @property
    def nombre(self) -> str:
        return self._nombre
    
    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = validar_con_patron(
            valor, "El nombre", PATRON_NOMBRE, ERROR_SOLO_LETRAS
        )

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor: str) -> None:
        self._descripcion = validar_texto(valor, "La descripción")

    @property
    def fecha_inicio(self) -> date:
        return self._fecha_inicio

    @fecha_inicio.setter
    def fecha_inicio(self, valor: date) -> None:
        if not isinstance(valor, date):
            raise TypeError("La fecha de inicio debe ser una instancia de date")
        self._fecha_inicio = valor

    @property
    def empleados(self) -> tuple:
        return tuple(self._empleados)

    def asignar_empleado(self, empleado: Empleado) -> None:
        if not isinstance(empleado, Empleado):
            raise TypeError("El empleado debe ser una instancia de la clase Empleado.")
        if any(e.id == empleado.id for e in self._empleados):
            raise ValueError(f"El empleado con id {empleado.id} ya participa en este proyecto.")
        self._empleados.append(empleado)
        empleado._agregar_proyecto(self)   # ← mantiene sincronizada la otra lista

    def quitar_empleado(self, empleado: Empleado) -> None:
        if not isinstance(empleado, Empleado):
            raise TypeError("El empleado debe ser una instancia de la clase Empleado.")
        if not any(e.id == empleado.id for e in self._empleados):
            raise ValueError(f"El empleado con id {empleado.id} no participa en este proyecto.")
        self._empleados = [e for e in self._empleados if e.id != empleado.id]
        empleado._quitar_proyecto(self)