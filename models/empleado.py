from datetime import date
from typing import TYPE_CHECKING
from .persona import Persona
from .registro_tiempo import RegistroTiempo

from .usuario import Usuario

if TYPE_CHECKING:
    from .proyecto import Proyecto
    from .rol import Rol

class Empleado(Persona):
    """Persona contratada por EcoTech.
    """

    def __init__(
        self,
        id: int | None,
        nombre: str,
        direccion: str,
        telefono: str,
        correo: str,
        rut: str,
        salario: float,
        fecha_inicio_contrato: date,
        activo:bool = True
    ) -> None:
        super().__init__(id, nombre, direccion, telefono, correo, rut)
        self._salario = salario
        self._fecha_inicio_contrato = fecha_inicio_contrato
        self._valor_proyectos = []  # lista de proyectos a los que pertenece el empleado
        self._valor_registros_tiempo = []  # lista de registros de tiempo del empleado
        self._valor_usuario = None
        self._activo = activo

    @property
    def _salario(self) -> float:
        return self._valor_salario

    @_salario.setter
    def _salario(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("El salario debe ser un número (int o float)")
        if valor < 0:
            raise ValueError("El salario no puede ser menor que 0")
        self._valor_salario = float(valor)


    @property
    def _fecha_inicio_contrato(self) -> date:
        return self._valor_fecha_inicio_contrato


    @_fecha_inicio_contrato.setter
    def _fecha_inicio_contrato(self, valor: date) -> None:
        if not isinstance(valor, date):
            raise TypeError("La fecha de inicio debe ser una instancia de date")
        self._valor_fecha_inicio_contrato = valor

    @property
    def _proyectos(self) -> tuple:
        return tuple(self._valor_proyectos)

    def listar_proyectos(self) -> tuple:
        return self._proyectos

    def _agregar_proyecto(self, proyecto: "Proyecto") -> None:
    # el guion bajo es una señal: "solo Proyecto.asignarEmpleado debería
    # llamar esto". Si alguien lo llama desde afuera sin pasar por ahí,
    # rompe la sincronía entre las dos listas.
        self._valor_proyectos.append(proyecto)

    def _quitar_proyecto(self, proyecto: "Proyecto") -> None:
        self._valor_proyectos = [p for p in self._valor_proyectos if p._id != proyecto._id]

    @property
    def _registros_tiempo(self) -> tuple:
        return tuple(self._valor_registros_tiempo)


    def registrar_horas(self, fecha: date, horas_trabajadas: float, descripcion: str, proyecto: "Proyecto") -> RegistroTiempo:
        # No permitir más de un registro por empleado y día
        if any(
            registro._fecha == fecha
            for registro in self._valor_registros_tiempo
        ):
            raise ValueError(
                f"El día {fecha} ya tiene un registro de horas."
            )

        horas_del_dia = sum(
            r._horas_trabajadas
            for r in self._valor_registros_tiempo
            if r._fecha == fecha
        )
        if horas_del_dia + horas_trabajadas > 10:
            raise ValueError(
                f"Con este registro se superarían las 10 horas diarias permitidas "
                f"({horas_del_dia}h ya registradas el {fecha})."
            )

        semana_nueva = fecha.isocalendar()[:2]  # (año ISO, número de semana) → lunes a domingo
        horas_de_la_semana = sum(
            r._horas_trabajadas for r in self._valor_registros_tiempo
            if r._fecha.isocalendar()[:2] == semana_nueva
        )
        if horas_de_la_semana + horas_trabajadas > 42:
            raise ValueError(
                f"Con este registro se superarían las 42 horas semanales permitidas "
                f"({horas_de_la_semana}h ya registradas esa semana)."
            )

        registro = RegistroTiempo(fecha, horas_trabajadas, descripcion, self, proyecto)
        self._valor_registros_tiempo.append(registro)
        return registro

    def crear_usuario(self, password: str, rol: "Rol") -> "Usuario":
        username = Usuario.generar_username(self._nombre)
        self._valor_usuario = Usuario(id=self._id, username=username, password=password, rol=rol)
        return self._valor_usuario

    @property
    def _usuario(self) -> "Usuario":
        return self._valor_usuario

    def _agregar_registro_tiempo(self, registro: "RegistroTiempo") -> None:
    # sin revalidar topes — se usa solo para reconstruir historial ya
    # validado desde la BD, no para registrar horas nuevas
        self._valor_registros_tiempo.append(registro)

    def _limpiar_registros_tiempo(self) -> None:
        self._valor_registros_tiempo.clear()

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