from datetime import date
from typing import TYPE_CHECKING
from .persona import Persona
from .registro_tiempo import RegistroTiempo

if TYPE_CHECKING:
    from .proyecto import Proyecto
    from .rol import Rol
    from .usuario import Usuario

class Empleado(Persona):
    """Persona contratada por EcoTech.
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
        self._proyectos = []  # lista de proyectos a los que pertenece el empleado
        self._registros_tiempo = []  # lista de registros de tiempo del empleado

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

    @property
    def proyectos(self) -> tuple:
        return tuple(self._proyectos)

    def listar_proyectos(self) -> tuple:
        return self.proyectos

    def _agregar_proyecto(self, proyecto: "Proyecto") -> None:
    # el guion bajo es una señal: "solo Proyecto.asignarEmpleado debería
    # llamar esto". Si alguien lo llama desde afuera sin pasar por ahí,
    # rompe la sincronía entre las dos listas.
        self._proyectos.append(proyecto)

    def _quitar_proyecto(self, proyecto: "Proyecto") -> None:
        self._proyectos = [p for p in self._proyectos if p.id != proyecto.id]

    @property
    def registros_tiempo(self) -> tuple:
        return tuple(self._registros_tiempo)


    def registrar_horas(self, fecha: date, horas_trabajadas: float, descripcion: str, proyecto: "Proyecto") -> RegistroTiempo:
        horas_del_dia = sum(r.horas_trabajadas for r in self._registros_tiempo if r.fecha == fecha)
        if horas_del_dia + horas_trabajadas > 10:
            raise ValueError(
                f"Con este registro se superarían las 10 horas diarias permitidas "
                f"({horas_del_dia}h ya registradas el {fecha})."
            )

        semana_nueva = fecha.isocalendar()[:2]  # (año ISO, número de semana) → lunes a domingo
        horas_de_la_semana = sum(
            r.horas_trabajadas for r in self._registros_tiempo
            if r.fecha.isocalendar()[:2] == semana_nueva
        )
        if horas_de_la_semana + horas_trabajadas > 42:
            raise ValueError(
                f"Con este registro se superarían las 42 horas semanales permitidas "
                f"({horas_de_la_semana}h ya registradas esa semana)."
            )

        registro = RegistroTiempo(fecha, horas_trabajadas, descripcion, self, proyecto)
        self._registros_tiempo.append(registro)
        return registro

    def crear_usuario(self, password: str, rol: "Rol") -> "Usuario":
        username = Usuario.generar_username(self.nombre)
        self._usuario = Usuario(id=self.id, username=username, password=password, rol=rol)
        return self._usuario

    @property
    def usuario(self) -> "Usuario":
        return self._usuario