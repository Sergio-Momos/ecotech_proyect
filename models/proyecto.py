from .empleado import Empleado
from utils.validaciones import validar_id, validar_con_patron, validar_texto
from utils.constantes import PATRON_NOMBRE, ERROR_SOLO_LETRAS
from datetime import date


class Proyecto:
    def __init__(self, id: int| None, nombre: str, descripcion: str, fecha_inicio: date, activo: bool = True):
        self._valor_id = None
        if id is not None:
            self._id = id
        self._nombre = nombre
        self._descripcion = descripcion
        self._fecha_inicio = fecha_inicio
        self._valor_empleados = []
        self._activo = activo
    
    @property
    def _id(self) -> int| None:
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
    def _descripcion(self) -> str:
        return self._valor_descripcion

    @_descripcion.setter
    def _descripcion(self, valor: str) -> None:
        self._valor_descripcion = validar_texto(valor, "La descripción")

    @property
    def _fecha_inicio(self) -> date:
        return self._valor_fecha_inicio

    @_fecha_inicio.setter
    def _fecha_inicio(self, valor: date) -> None:
        if not isinstance(valor, date):
            raise TypeError("La fecha de inicio debe ser una instancia de date")
        self._valor_fecha_inicio = valor

    @property
    def _empleados(self) -> tuple:
        return tuple(self._valor_empleados)

    def asignar_empleado(self, empleado: Empleado) -> None:
        if not isinstance(empleado, Empleado):
            raise TypeError("El empleado debe ser una instancia de la clase Empleado.")
        if any(e._id == empleado._id for e in self._valor_empleados):
            raise ValueError(f"El empleado con id {empleado._id} ya participa en este proyecto.")
        self._valor_empleados.append(empleado)
        empleado._agregar_proyecto(self)   # ← mantiene sincronizada la otra lista

    def quitar_empleado(self, empleado: Empleado) -> None:
        if not isinstance(empleado, Empleado):
            raise TypeError("El empleado debe ser una instancia de la clase Empleado.")
        if not any(e._id == empleado._id for e in self._valor_empleados):
            raise ValueError(f"El empleado con id {empleado._id} no participa en este proyecto.")
        self._valor_empleados = [e for e in self._valor_empleados if e._id != empleado._id]
        empleado._quitar_proyecto(self)

    @property
    def _activo(self) -> bool:
        return self._valor_activo

    @_activo.setter
    def _activo(self, valor: bool) -> None:
        if not isinstance(valor, bool):
            raise TypeError("El estado activo debe ser un booleano.")
        self._valor_activo = valor

    def desactivar(self) -> None:
        self._activo = False

    def activar(self) -> None:
        self._activo = True