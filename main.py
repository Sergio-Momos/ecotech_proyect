from datetime import date

from database.conexion import probar_conexion, establecer_perfil_activo
from models.empleado import Empleado
from models.rol import Rol
from repositorios import empleado_repo, rol_repo, usuario_repo, departamento_repo
from models.departamento import Departamento

def separador(titulo: str) -> None:
    print("\n" + "=" * 60)
    print(titulo)
    print("=" * 60)


def main():

    separador("Conexión a MySQL")
    separador("Probando los tres perfiles de conexión")
    for perfil in ("auth", "empleado", "rrhh"):
        try:
            probar_conexion(perfil)
            print(f"  {perfil}: conexión exitosa")
        except Exception as e:
            print(f"  {perfil}: FALLÓ -> {e}")

    # Este script actúa como administrador para poblar datos iniciales —
    # no es un usuario autenticado, así que elegir el perfil acá es
    # explícito y correcto, no una excepción a la regla de seguridad.
    establecer_perfil_activo("rrhh")
    separador("Sembrando datos base para la GUI (idempotente)")

    # --- Rol RRHH: crear solo si no existe ---
    rol_rrhh = rol_repo.buscar_por_nombre("Recursos Humanos")
    if rol_rrhh is None:
        rol_rrhh = Rol.recursos_humanos()
        rol_repo.crear(rol_rrhh)
        print(f"Rol creado -> id: {rol_rrhh.id}")
    else:
        print(f"Rol ya existía -> id: {rol_rrhh.id}")

    # --- Empleado base: reutiliza el primero que encuentre, o crea uno ---
    empleados = empleado_repo.listar_todos()
    if empleados:
        empleado = empleados[0]
        print(f"Reutilizando empleado existente -> id: {empleado.id}, {empleado.nombre}")
    else:
        empleado = Empleado(
            id=None, nombre="Admin Principal", direccion="Oficina Central 1",
            telefono="900000000", correo="admin@ecotech.cl",
            rut="21.456.789-K", salario=900000, fecha_inicio_contrato=date(2024, 1, 1),
        )
        empleado_repo.crear(empleado)
        print(f"Empleado creado -> id: {empleado.id}")

    # --- Usuario para ese empleado: solo si todavía no tiene uno ---
    usuario = usuario_repo.buscar_por_id(empleado.id)
    if usuario is None:
        usuario = usuario_repo.crear_para_empleado(empleado, password="Clave#2024", rol=rol_rrhh)  # NOSONAR
        print(f"Usuario creado -> username: {usuario.username}")
    else:
        print(f"Usuario ya existía -> username: {usuario.username}")

    print("\nListo — puedes iniciar sesión en la GUI con:")
    print(f"  username: {usuario.username}")
    print(f"  password: Clave#2024")# NOSONAR

    separador("Sembrando más datos de prueba")

    empleados_existentes = empleado_repo.listar_todos()
    nombres_existentes = {e.nombre for e in empleados_existentes}

    datos_nuevos = [
        ("Ana Torres", "Los Alerces 123", "912345678", "ana.torres@ecotech.cl", "11.111.111-1", 650000, date(2023, 3, 1)),
        ("Juan Perez", "Neptuno 097", "987654321", "juan.perez@ecotech.cl", "22.222.222-2", 580000, date(2024, 6, 15)),
        ("Camila Rios", "Av. Siempre Viva 742", "933333333", "camila.rios@ecotech.cl", "18.765.432-7", 725450, date(2024, 4, 20)),
    ]

    for nombre, direccion, telefono, correo, rut, salario, fecha in datos_nuevos:
        if nombre in nombres_existentes:
            print(f"{nombre} ya existía, se omite.")
            continue
        nuevo = Empleado(
            id=None, nombre=nombre, direccion=direccion, telefono=telefono,
            correo=correo, rut=rut, salario=salario, fecha_inicio_contrato=fecha,
        )
        empleado_repo.crear(nuevo)
        print(f"Empleado creado: {nombre} -> id {nuevo.id}")

    # --- Rol Empleado estándar: crear si no existe ---
    rol_empleado = rol_repo.buscar_por_nombre("Empleado")
    if rol_empleado is None:
        rol_empleado = Rol.empleado_estandar()
        rol_repo.crear(rol_empleado)
        print(f"Rol 'Empleado' creado -> id: {rol_empleado.id}")

    # --- Departamento de ejemplo, con Ana como gerente ---
    empleados_por_nombre = {e.nombre: e for e in empleado_repo.listar_todos()}
    ana = empleados_por_nombre.get("Ana Torres")
    juan = empleados_por_nombre.get("Juan Perez")

    depto_existente = next((d for d in departamento_repo.listar_todos() if d.nombre == "RecursosHumanos"), None)
    if depto_existente is None and ana is not None:
        depto = Departamento(id=None, nombre="RecursosHumanos", gerente=ana)
        departamento_repo.crear(depto)
        if juan is not None:
            departamento_repo.asignar_empleado(depto.id, juan.id)
        print(f"Departamento creado -> id: {depto.id}")

    # --- Usuario con rol Empleado estándar, para probar esa vista más adelante ---
    if juan is not None:
        usuario_juan = usuario_repo.buscar_por_id(juan.id)
        if usuario_juan is None:
            usuario_juan = usuario_repo.crear_para_empleado(juan, password="Empleado#1", rol=rol_empleado)  # NOSONAR
            print(f"Usuario (Empleado estándar) creado -> username: {usuario_juan.username}")

if __name__ == "__main__":
    main()