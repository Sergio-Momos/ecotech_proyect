from .empleado import Empleado
from utils.constantes import PATRON_NOMBRE, ERROR_SOLO_LETRAS
from utils.validaciones import validar_con_patron, validar_id


class Departamento:
    def __init__(self, id: int, nombre: str, gerente: Empleado) -> None:
        validar_id(id, "El id")
        self._id = id
        self.nombre = nombre
        self._empleados = []
        self.gerente = gerente

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
    def gerente(self) -> Empleado:
        return self._gerente

    @gerente.setter
    def gerente(self, valor: Empleado) -> None:
        if not isinstance(valor, Empleado):
            raise TypeError("El gerente debe ser una instancia de la clase Empleado.")
        self._gerente = valor

    @property
    def empleados(self) -> tuple:
        return tuple(self._empleados)   # copia — nadie le hace .append() por fuera

    def agregar_empleado(self, empleado: Empleado) -> None:
        if not isinstance(empleado, Empleado):
            raise TypeError("El empleado debe ser una instancia de la clase Empleado.")
        if any(e.id == empleado.id for e in self._empleados):
            raise ValueError(f"El empleado con id {empleado.id} ya pertenece a este departamento.")
        self._empleados.append(empleado)

    def eliminar_empleado(self, empleado: Empleado) -> None:
        if not isinstance(empleado, Empleado):
            raise TypeError("El empleado debe ser una instancia de la clase Empleado.")
                
        for e in self._empleados:
            if e.id == empleado.id:
                self._empleados.remove(e)
                return  # Termina la ejecución tras eliminarlo
                    
            # Si el ciclo termina sin encontrarlo:
        raise ValueError(f"El empleado con id {empleado.id} no pertenece a este departamento.")

    def buscar_empleado(self, id: int) -> Empleado:
        validar_id(id, "El id")
        for e in self._empleados:
            if e.id == id:
                return e
        raise ValueError(f"No se encontró un empleado con id {id} en este departamento.")

    def reasignar_empleado(self, empleado: Empleado, destino: "Departamento") -> None:
        if not isinstance(destino, Departamento):
            raise TypeError("El destino debe ser una instancia de la clase Departamento.")
                
    # Reutilizamos la lógica ya creada
        self.eliminar_empleado(empleado)
        destino.agregar_empleado(empleado)
