"""Siembra idempotente de datos ficticios para pruebas locales.

Uso: python main.py --seed-demo
No vacía tablas ni elimina datos existentes.
"""

from datetime import date
import argparse
from database.conexion import establecer_perfil_activo
from models.empleado import Empleado
from models.rol import Rol
from models.departamento import Departamento
from models.proyecto import Proyecto
from repositorios import empleado_repo, rol_repo, usuario_repo, departamento_repo, proyecto_repo

PASSWORDS_DEMO = {
    "rrhh": "Admin#2024",
    "ti": "TI#Clave2024",
    "empleado": "Empleado#1",
}


def sembrar_roles() -> dict:
    print("\n--- Roles ---")
    roles = {}
    for factory, clave in [
        (Rol.recursos_humanos, "rrhh"),
        (Rol.empleado_estandar, "empleado"),
        (Rol.ti, "ti"),
    ]:
        rol_base = factory()
        rol = rol_repo.buscar_por_nombre(rol_base._nombre)
        if rol is None:
            rol = rol_base
            rol_repo.crear(rol)
            print(f"  Creado: {rol._nombre} (id: {rol._id})")
        else:
            # Resincronizar permisos por si cambiaron en el código
            faltantes = rol_base._permisos - rol._permisos
            if faltantes:
                for p in faltantes:
                    rol.agregar_permiso(p)
                rol_repo.actualizar(rol)
                print(f"  Actualizado: {rol._nombre} (+{len(faltantes)} permisos)")
            else:
                print(f"  Ya existía: {rol._nombre} (id: {rol._id})")
        roles[clave] = rol
    return roles


def sembrar_empleados(roles: dict) -> dict:
    print("\n--- Empleados base ---")
    datos = [
        ("Demo", "Admin", "Dirección de prueba 1", "900000001", "admin@demo.invalid", "21.456.789-K", 900000, date(2024, 1, 1), "rrhh"),
        ("Demo", "Soporte", "Dirección de prueba 2", "900000002", "ti@demo.invalid", "22.261.674-3", 800000, date(2024, 1, 1), "ti"),
        ("Ana", "Prueba", "Dirección de prueba 3", "900000003", "ana@demo.invalid", "11.111.111-1", 650000, date(2023, 3, 1), "empleado"),
        ("Juan", "Ejemplo", "Dirección de prueba 4", "900000004", "juan@demo.invalid", "22.222.222-2", 580000, date(2024, 6, 15), "empleado"),
        ("Camila", "Demo", "Dirección de prueba 5", "900000005", "camila@demo.invalid", "18.765.432-7", 725450, date(2024, 4, 20), "empleado"),
    ]

    creados = {}
    for nombre, apellido, dir, tel, correo, rut, salario, fecha, rol_clave in datos:
        nombre_completo = f"{nombre} {apellido}"
        existentes = empleado_repo.listar_todos(incluir_inactivos=True)
        emp = next((e for e in existentes if e.get_nombre_completo() == nombre_completo), None)
        if emp is None:
            # Buscar por RUT también reconoce cuentas TI ocultas en la lista habitual.
            emp = empleado_repo.buscar_por_rut(rut)
        if emp is not None:
            print(f"  Ya existía: {nombre_completo} (id: {emp._id})")
        else:
            emp = Empleado(
                id=None, nombre=nombre, apellido=apellido, direccion=dir, telefono=tel,
                correo=correo, rut=rut, salario=salario,
                fecha_inicio_contrato=fecha,
            )
            empleado_repo.crear(emp)
            print(f"  Creado: {nombre_completo} (id: {emp._id})")
        creados[nombre_completo] = (emp, rol_clave)
    return creados

def sembrar_usuarios(empleados_roles: dict, roles: dict) -> None:
    print("\n--- Usuarios ---")
    for nombre, (emp, rol_clave) in empleados_roles.items():
        usuario = usuario_repo.buscar_por_id(emp._id)
        if usuario is not None:
            print(f"  Ya existía: {usuario._username}")
        else:
            usuario = usuario_repo.crear_para_empleado(
                emp,
                password=PASSWORDS_DEMO[rol_clave],
                rol=roles[rol_clave],
            )
            print(f"  Creado: {usuario._username}")


def sembrar_departamento(empleados_roles: dict) -> None:
    print("\n--- Departamento base ---")
    existentes = departamento_repo.listar_todos()
    if any(d._nombre == "RecursosHumanos" for d in existentes):
        print("  Ya existía: RecursosHumanos")
        return
    ana = empleados_roles.get("Ana Prueba")
    if ana is None:
        print("  Ana Prueba no encontrada, se omite el departamento.")
        return
    emp_ana = ana[0]
    depto = Departamento(id=None, nombre="RecursosHumanos", gerente=emp_ana)
    departamento_repo.crear(depto)
    juan = empleados_roles.get("Juan Ejemplo")
    if juan:
        departamento_repo.asignar_empleado(depto._id, juan[0]._id)
    print(f"  Creado: RecursosHumanos (id: {depto._id})")


def sembrar_proyecto(empleados_roles: dict) -> None:
    print("\n--- Proyecto base ---")
    existentes = proyecto_repo.listar_todos(incluir_inactivos=True)
    if any(p._nombre == "PanelesSolares" for p in existentes):
        print("  Ya existía: PanelesSolares")
        return
    proyecto = Proyecto(
        id=None, nombre="PanelesSolares",
        descripcion="Instalacion de paneles solares en oficina central",
        fecha_inicio=date.today(),
    )
    proyecto_repo.crear(proyecto)
    for nombre in ("Ana Prueba", "Camila Demo"):
        emp_info = empleados_roles.get(nombre)
        if emp_info:
            proyecto_repo.asignar_empleado(proyecto._id, emp_info[0]._id)
    print(f"  Creado: PanelesSolares (id: {proyecto._id})")


def main():
    parser = argparse.ArgumentParser(description="Siembra idempotente de datos ficticios para pruebas.")
    parser.add_argument(
        "--seed-demo", action="store_true",
        help="crear los registros demo sin borrar los datos existentes",
    )
    args = parser.parse_args()
    if not args.seed_demo:
        parser.error("debes indicar --seed-demo; esta herramienta nunca trunca la base de datos")

    print("=" * 50)
    print("  EcoTech RRHH — Siembra de datos base")
    print("=" * 50)

    # El script de siembra actúa como administrador explícitamente —
    # no es un usuario autenticado, así que elegir el perfil acá es
    # correcto (ver notas de arquitectura en database/conexion.py).
    establecer_perfil_activo("rrhh")

    roles = sembrar_roles()
    empleados_roles = sembrar_empleados(roles)
    sembrar_usuarios(empleados_roles, roles)
    sembrar_departamento(empleados_roles)
    sembrar_proyecto(empleados_roles)

    print("\n" + "=" * 50)
    print("  Siembra completada.")
    print("\n  Contraseñas demo: RRHH Admin#2024 · TI TI#Clave2024 · Empleados Empleado#1")
    print("  La siembra es idempotente y no borra datos existentes.")
    print("=" * 50)


if __name__ == "__main__":
    main()
