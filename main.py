from models.empleado import Empleado
from datetime import date

empleado1 = Empleado(
    1,
    "Ana Pérez",
    "Calle 123",
    "912345678",
    "ana@ecotech.cl",
    "22261674-3",
    5000000,
    date(2023, 1, 1)
)


print(empleado1)

for atributo, valor in empleado1.__dict__.items():
    print(f"{atributo}: {valor}")