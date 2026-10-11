from .empleado import Empleado
from utils.constantes import PATRON_NOMBRE, ERROR_SOLO_LETRAS
from utils.validaciones import validar_con_patron, validar_id


class Departamento:
    def __init__(self, id: int | None, nombre: str, gerente: Empleado) -> None:
        self._valor_id = None
        if id is not None:
            self._id = id
        self._nombre = nombre
        self._valor_empleados = []
        self._gerente = gerente

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
    def _gerente(self) -> Empleado:
        return self._valor_gerente

    @_gerente.setter
    def _gerente(self, valor: Empleado) -> None:
        if not isinstance(valor, Empleado):
            raise TypeError("El gerente debe ser una instancia de la clase Empleado.")
        self._valor_gerente = valor

    @property
    def _empleados(self) -> tuple:
        return tuple(self._valor_empleados)   # copia — nadie le hace .append() por fuera

    def agregar_empleado(self, empleado: Empleado) -> None:
        if not isinstance(empleado, Empleado):
            raise TypeError("El empleado debe ser una instancia de la clase Empleado.")
        if any(e._id == empleado._id for e in self._valor_empleados):
            raise ValueError(f"El empleado con id {empleado._id} ya pertenece a este departamento.")
        self._valor_empleados.append(empleado)

    def eliminar_empleado(self, empleado: Empleado) -> None:
        if not isinstance(empleado, Empleado):
            raise TypeError("El empleado debe ser una instancia de la clase Empleado.")
                
        for e in self._valor_empleados:
            if e._id == empleado._id:
                self._valor_empleados.remove(e)
                return  # Termina la ejecución tras eliminarlo
                    
            # Si el ciclo termina sin encontrarlo:
        raise ValueError(f"El empleado con id {empleado._id} no pertenece a este departamento.")

    def buscar_empleado(self, id: int) -> Empleado:
        validar_id(id, "El id")
        for e in self._valor_empleados:
            if e._id == id:
                return e
        raise ValueError(f"No se encontró un empleado con id {id} en este departamento.")

    def reasignar_empleado(self, empleado: Empleado, destino: "Departamento") -> None:
        if not isinstance(destino, Departamento):
            raise TypeError("El destino debe ser una instancia de la clase Departamento.")
                
    # Reutilizamos la lógica ya creada
        self.eliminar_empleado(empleado)
        destino.agregar_empleado(empleado)
