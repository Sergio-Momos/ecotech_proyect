from persona import Persona

from datetime import date

class Empleado(Persona):
    def __init__(self, id, nombre, direccion, telefono, correo, rut, salario, fecha_inicio_contrato):
        super().__init__(id, nombre, direccion, telefono, correo, rut)
        self._salario = salario
        self._fecha_inicio_contrato = fecha_inicio_contrato

    @property
    def salario(self) -> float:
        return self._salario

    @salario.setter
    def salario(self, valor: float):
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise TypeError("El salario debe ser un número (int o float)")
        if valor < 0:
            raise ValueError("El salario no puede ser menor que 0")
        self._salario = valor


    @property
    def fecha_inicio_contrato(self) -> date:
        return self._fecha_inicio_contrato



    @fecha_inicio_contrato.setter
    def fecha_inicio_contrato(self, valor: date):
        if not isinstance(valor, date):
            raise TypeError("La fecha de inicio debe ser una instancia de date")
        self._fecha_inicio_contrato = valor



empleado1 = Empleado(
    "1",
    "Sergio",
    "Neptuno 097",
    "95823782",
    "SI.com",
    "22230o2",
    5000.1,
    date(2026, 11, 6),
)

print(empleado1)

for atributo, valor in empleado1.__dict__.items():
    print(f"{atributo}: {valor}")