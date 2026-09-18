from models.empleado import Empleado
from datetime import date

from models.usuario import Usuario

from models.departamento import Departamento

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

empleado2 = Empleado(
    2,
    "Luis Hernández",
    "Calle 456",
    "987654321",
    "luis@ecotech.cl",
    "22261674-3",
    5000000,
    date(2023, 1, 1)
)

empleado3 = Empleado(
    3,
    "María García",
    "Calle 789",
    "955555555",
    "maria@ecotech.cl",
    "22261674-3",
    5000000,
    date(2023, 1, 1)
)

empleado4 = Empleado(
    4,
    "Carlos López",
    "Calle 101",
    "966666666",
    "carlos@ecotech.cl",
    "22261674-3",
    5000000,
    date(2023, 1, 1)
)

print(empleado1)

for atributo, valor in empleado1.__dict__.items():
    print(f"{atributo}: {valor}")


print("\n--- Probando la clase Usuario ---")
usuario1 = Usuario(1, "A.perez", "Password123!")
usuario2 = Usuario(1, "L.Hayquetin", "Password123!")

print(usuario1._password)

print(usuario2._password)


print("\n--- Probando la clase Departamento ---")

departamento1 = Departamento(1, "Recursos Humanos", empleado1)

departamento2 = Departamento(2, "Finanzas", empleado2)

departamento1.agregar_empleado(empleado2)
departamento1.agregar_empleado(empleado3)
departamento2.agregar_empleado(empleado4)

print(f"Departamento: {departamento1.nombre}, Gerente: {departamento1.gerente.nombre} Empleados: {[e.nombre for e in departamento1.empleados]}")

print("\n--- Probando la clase Departamento: eliminar empleado---")

departamento1.eliminar_empleado(empleado2)

print(f"Departamento: {departamento1.nombre}, Gerente: {departamento1.gerente.nombre} Empleados: {[e.nombre for e in departamento1.empleados]}")

print("\n--- Probando la clase Departamento: reasignar empleado---")


print(f"Departamento: {departamento2.nombre}, Gerente: {departamento2.gerente.nombre} Empleados: {[e.nombre for e in departamento2.empleados]}")

departamento1.reasignar_empleado(empleado3, departamento2)

print(f"Departamento: {departamento1.nombre}, Gerente: {departamento1.gerente.nombre} Empleados: {[e.nombre for e in departamento1.empleados]}")

print(f"Departamento: {departamento2.nombre}, Gerente: {departamento2.gerente.nombre} Empleados: {[e.nombre for e in departamento2.empleados]}")