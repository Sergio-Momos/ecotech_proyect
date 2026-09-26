"""
seed.py — Siembra datos base para EcoTech RRHH.
Corre UNA VEZ por instalación nueva, desde la raíz del proyecto:

    python seed.py

Requisitos previos:
  1. Tener el .env con FERNET_KEY y credenciales de MySQL (pedir al equipo).
  2. Haber corrido database/esquema.sql en tu MySQL.
  3. Haber corrido database/roles_mysql.sql en tu MySQL (con cuenta admin).
"""

from datetime import date
from database.conexion import establecer_perfil_activo
from models.empleado import Empleado
from models.rol import Rol
from models.departamento import Departamento
from models.proyecto import Proyecto
from repositorios import empleado_repo, rol_repo, usuario_repo, departamento_repo, proyecto_repo


def sembrar_roles() -> dict:
    print("\n--- Roles ---")
    roles = {}
    for factory, clave in [
        (Rol.recursos_humanos, "rrhh"),
        (Rol.empleado_estandar, "empleado"),
        (Rol.ti, "ti"),
    ]:
        rol = rol_repo.buscar_por_nombre(factory().nombre)
        if rol is None:
            rol = factory()
            rol_repo.crear(rol)
            print(f"  Creado: {rol.nombre} (id: {rol.id})")
        else:
            # Resincronizar permisos por si cambiaron en el código
            faltantes = factory().permisos - rol.permisos
            if faltantes:
                for p in faltantes:
                    rol.agregar_permiso(p)
                rol_repo.actualizar(rol)
                print(f"  Actualizado: {rol.nombre} (+{len(faltantes)} permisos)")
            else:
                print(f"  Ya existía: {rol.nombre} (id: {rol.id})")
        roles[clave] = rol
    return roles


def sembrar_empleados(roles: dict) -> dict:
    print("\n--- Empleados base ---")
    datos = [
        ("Admin Principal",  "Oficina Central 1",  "900000001", "admin@ecotech.cl",      "21.456.789-K", 900000, date(2024, 1, 1),  "rrhh"),
        ("Soporte TI",       "Oficina Central 2",  "900000002", "ti@ecotech.cl",          "20.333.444-3", 800000, date(2024, 1, 1),  "ti"),
        ("Ana Torres",       "Los Alerces 123",    "912345678", "ana.torres@ecotech.cl",  "11.111.111-1", 650000, date(2023, 3, 1),  "empleado"),
        ("Juan Perez",       "Neptuno 097",        "987654321", "juan.perez@ecotech.cl",  "22.222.222-2", 580000, date(2024, 6, 15), "empleado"),
        ("Camila Rios",      "Av. Siempre Viva 742","933333333","camila.rios@ecotech.cl", "18.765.432-7", 725450, date(2024, 4, 20), "empleado"),
    ]

    creados = {}
    for nombre, dir, tel, correo, rut, salario, fecha, rol_clave in datos:
        existentes = empleado_repo.listar_todos(incluir_inactivos=True)
        if any(e.nombre == nombre for e in existentes):
            emp = next(e for e in existentes if e.nombre == nombre)
            print(f"  Ya existía: {nombre} (id: {emp.id})")
        else:
            emp = Empleado(
                id=None, nombre=nombre, direccion=dir, telefono=tel,
                correo=correo, rut=rut, salario=salario,
                fecha_inicio_contrato=fecha,
            )
            empleado_repo.crear(emp)
            print(f"  Creado: {nombre} (id: {emp.id})")
        creados[nombre] = (emp, rol_clave)
    return creados


def sembrar_usuarios(empleados_roles: dict, roles: dict) -> None:
    print("\n--- Usuarios ---")
    contrasenas = {
        "rrhh":     "Admin#2024",
        "ti":       "TI#Clave2024",
        "empleado": "Empleado#1",
    }
    for nombre, (emp, rol_clave) in empleados_roles.items():
        usuario = usuario_repo.buscar_por_id(emp.id)
        if usuario is not None:
            print(f"  Ya existía: {usuario.username}")
        else:
            usuario = usuario_repo.crear_para_empleado(
                emp,
                password=contrasenas[rol_clave],
                rol=roles[rol_clave],
            )
            print(f"  Creado: {usuario.username}  (contraseña inicial: {contrasenas[rol_clave]})")


def sembrar_departamento(empleados_roles: dict) -> None:
    print("\n--- Departamento base ---")
    existentes = departamento_repo.listar_todos()
    if any(d.nombre == "RecursosHumanos" for d in existentes):
        print("  Ya existía: RecursosHumanos")
        return
    ana = empleados_roles.get("Ana Torres")
    if ana is None:
        print("  Ana Torres no encontrada, se omite el departamento.")
        return
    emp_ana = ana[0]
    depto = Departamento(id=None, nombre="RecursosHumanos", gerente=emp_ana)
    departamento_repo.crear(depto)
    juan = empleados_roles.get("Juan Perez")
    if juan:
        departamento_repo.asignar_empleado(depto.id, juan[0].id)
    print(f"  Creado: RecursosHumanos (id: {depto.id})")


def sembrar_proyecto(empleados_roles: dict) -> None:
    print("\n--- Proyecto base ---")
    existentes = proyecto_repo.listar_todos(incluir_inactivos=True)
    if any(p.nombre == "PanelesSolares" for p in existentes):
        print("  Ya existía: PanelesSolares")
        return
    proyecto = Proyecto(
        id=None, nombre="PanelesSolares",
        descripcion="Instalacion de paneles solares en oficina central",
        fecha_inicio=date(2024, 1, 10),
    )
    proyecto_repo.crear(proyecto)
    for nombre in ("Ana Torres", "Camila Rios"):
        emp_info = empleados_roles.get(nombre)
        if emp_info:
            proyecto_repo.asignar_empleado(proyecto.id, emp_info[0].id)
    print(f"  Creado: PanelesSolares (id: {proyecto.id})")


def main():
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
    print("\n  Credenciales iniciales:")
    print("  Admin RRHH  → username generado  / Admin#2024")
    print("  Soporte TI  → username generado  / TI#Clave2024")
    print("  Empleados   → username generado  / Empleado#1")
    print("\n  Los usernames exactos aparecen arriba en 'Usuarios'.")
    print("=" * 50)


if __name__ == "__main__":
    main()