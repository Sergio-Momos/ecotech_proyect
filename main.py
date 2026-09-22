from datetime import date

from models.empleado import Empleado
from models.departamento import Departamento
from models.proyecto import Proyecto
from models.rol import Rol
from models.usuario import Usuario
from models.seguridad import Seguridad
from database.conexion import probar_conexion


def separador(titulo: str) -> None:
    print("\n" + "=" * 60)
    print(titulo)
    print("=" * 60)


def main():
    # --- 1. Empleados (Persona + herencia) ---
    separador("1. Creando empleados (en memoria)")
    ana = Empleado(
        id=1, nombre="Ana Torres", direccion="Los Alerces 123",
        telefono="912345678", correo="ana.torres@ecotech.cl",
        rut="111111111", salario=650000, fecha_inicio_contrato=date(2023, 3, 1),
    )
    juan = Empleado(
        id=2, nombre="Juan Perez", direccion="Neptuno 097",
        telefono="987654321", correo="juan.perez@ecotech.cl",
        rut="222222222", salario=580000, fecha_inicio_contrato=date(2024, 6, 15),
    )
    print(ana)
    print(juan)

    # --- 2. Departamento (agregación, en memoria) ---
    separador("2. Departamento (en memoria)")
    rrhh = Departamento(id=1, nombre="RecursosHumanos", gerente=ana)
    rrhh.agregar_empleado(ana)
    rrhh.agregar_empleado(juan)
    print(f"Departamento: {rrhh.nombre} | Gerente: {rrhh.gerente.get_nombre_completo()}")

    # --- 3. Proyecto (N:M, en memoria) ---
    separador("3. Proyecto (en memoria)")
    proyecto_solar = Proyecto(
        id=1, nombre="PanelesSolares",
        descripcion="Instalacion de paneles solares en oficina central",
        fecha_inicio=date(2024, 1, 10),
    )
    proyecto_solar.asignar_empleado(ana)
    print(f"Participantes: {[e.get_nombre_completo() for e in proyecto_solar.empleados]}")

    # --- 4. RegistroTiempo (composición) + topes legales, en memoria ---
    separador("4. Registro de horas (en memoria) + tope diario")
    ana.registrar_horas(date(2024, 9, 2), 6, "Instalacion de paneles", proyecto_solar)
    print("\nProbando tope diario (debería rechazar):")
    try:
        ana.registrar_horas(date(2024, 9, 2), 6, "Horas extra el mismo dia", proyecto_solar)
    except ValueError as e:
        print(f"  Rechazado correctamente -> {e}")

    # --- 5. Usuario + Rol + Seguridad ---
    separador("5. Usuario, Rol y Seguridad")
    rol_rrhh = Rol.recursos_humanos()
    rol_empleado = Rol.empleado_estandar()
    print(f"Rol RRHH: permisos={rol_rrhh.permisos}")
    print(f"Rol Empleado: permisos={rol_empleado.permisos}")

    usuario_ana = Usuario(id=1, username="a.torres", password="Clave#2024", rol=rol_rrhh)  # NOSONAR
    print("\nVerificando login:")
    print("  Clave correcta   ->", Seguridad.verificar_password("Clave#2024", usuario_ana._password))
    print("  Clave incorrecta ->", Seguridad.verificar_password("otraClave", usuario_ana._password))

    # --- 6. crear_usuario end-to-end, con colisión de nombres ---
    separador("6. crear_usuario (Empleado -> Usuario, con colisión)")
    usuario_de_ana = ana.crear_usuario(password="ClaveAna#1", rol=rol_rrhh)  # NOSONAR
    print(f"Usuario generado para Ana: {usuario_de_ana.username}")

    sergio1 = Empleado(
        id=3, nombre="Sergio Morales", direccion="Calle Uno 111",
        telefono="911111111", correo="sergio1@ecotech.cl",
        rut="333333333", salario=600000, fecha_inicio_contrato=date(2024, 1, 1),
    )
    sergio2 = Empleado(
        id=4, nombre="Sergio Morales", direccion="Calle Dos 222",
        telefono="922222222", correo="sergio2@ecotech.cl",
        rut="444444444", salario=610000, fecha_inicio_contrato=date(2024, 2, 1),
    )
    usuario1 = sergio1.crear_usuario(password="ClaveUno#1", rol=rol_empleado)  # NOSONAR
    usuario2 = sergio2.crear_usuario(password="ClaveDos#1", rol=rol_empleado)  # NOSONAR
    assert usuario1.username != usuario2.username, "¡Colisión no resuelta!"
    print(f"Colisión resuelta: {usuario1.username} / {usuario2.username}")

    # --- 7. Conexion a MySQL ---
    separador("7. Conexion a MySQL")
    if probar_conexion():
        print("Conexión exitosa a la base de datos.")

    # ================================================================
    # A partir de acá, todo pasa por los repositorios contra MySQL real
    # ================================================================
    from repositorios import empleado_repo, departamento_repo, proyecto_repo, registro_tiempo_repo

    # --- 8. empleado_repo: crear dos empleados reales para el resto de las pruebas ---
    separador("8. empleado_repo: creando empleados de prueba")
    camila = Empleado(
        id=None, nombre="Camila Rios", direccion="Av. Siempre Viva 742",
        telefono="933333333", correo="camila.rios@ecotech.cl",
        rut="18.765.432-7", salario=725450.50, fecha_inicio_contrato=date(2024, 4, 20),
    )
    pedro = Empleado(
        id=None, nombre="Pedro Soto", direccion="Los Aromos 55",
        telefono="955555555", correo="pedro.soto@ecotech.cl",
        rut="19.876.543-0", salario=690000, fecha_inicio_contrato=date(2024, 5, 2),
    )
    empleado_repo.crear(camila)
    empleado_repo.crear(pedro)
    print(f"Camila -> id: {camila.id} | Pedro -> id: {pedro.id}")

    print("\nProbando RUT duplicado (debería rechazar):")
    try:
        empleado_repo.crear(Empleado(
            id=None, nombre="Otro Nombre", direccion="Otra 123",
            telefono="944444444", correo="otro@ecotech.cl",
            rut="187654327",  # mismo RUT de Camila, sin puntos ni guion
            salario=500000, fecha_inicio_contrato=date(2024, 1, 1),
        ))
    except ValueError as e:
        print(f"  Rechazado correctamente -> {e}")

    recuperada = empleado_repo.buscar_por_id(camila.id)
    print(f"Releída desde la BD: {recuperada} | correo coincide: {recuperada.correo == camila.correo}")

    # --- 9. departamento_repo: crear, asignar empleados, actualizar ---
    separador("9. departamento_repo")
    depto = Departamento(id=None, nombre="Operaciones", gerente=camila)
    departamento_repo.crear(depto)
    print(f"Departamento creado -> id: {depto.id}")

    departamento_repo.asignar_empleado(depto.id, pedro.id)
    depto_recuperado = departamento_repo.buscar_por_id(depto.id)
    print(f"Gerente recuperado: {depto_recuperado.gerente.get_nombre_completo()}")
    print(f"Empleados del depto: {[e.get_nombre_completo() for e in depto_recuperado.empleados]}")
    assert any(e.id == pedro.id for e in depto_recuperado.empleados), "Pedro no quedó asignado."

    depto_recuperado.nombre = "OperacionesTecnicas"
    departamento_repo.actualizar(depto_recuperado)
    print(f"Nombre tras actualizar: {departamento_repo.buscar_por_id(depto.id).nombre}")

    # --- 10. proyecto_repo: crear, asignar N:M, borrado lógico ---
    separador("10. proyecto_repo")
    proyecto = Proyecto(
        id=None, nombre="ExpansionSolar",
        descripcion="Segunda etapa de paneles solares",
        fecha_inicio=date(2025, 1, 15),
    )
    proyecto_repo.crear(proyecto)
    proyecto_repo.asignar_empleado(proyecto.id, camila.id)
    proyecto_repo.asignar_empleado(proyecto.id, pedro.id)

    proyecto_recuperado = proyecto_repo.buscar_por_id(proyecto.id)
    print(f"Participantes: {[e.get_nombre_completo() for e in proyecto_recuperado.empleados]}")
    assert len(proyecto_recuperado.empleados) == 2

    print("\nProbando borrado lógico con un proyecto aparte:")
    proyecto_temporal = Proyecto(
        id=None, nombre="PilotoDescartable",
        descripcion="Proyecto de prueba para el borrado logico",
        fecha_inicio=date(2025, 2, 1),
    )
    proyecto_repo.crear(proyecto_temporal)
    proyecto_repo.eliminar(proyecto_temporal.id)
    activos = proyecto_repo.listar_todos()
    todos = proyecto_repo.listar_todos(incluir_inactivos=True)
    print(f"  Aparece en listar_todos() por defecto? {any(p.id == proyecto_temporal.id for p in activos)}")
    print(f"  Aparece incluyendo inactivos?          {any(p.id == proyecto_temporal.id for p in todos)}")
    print(f"  Sigue siendo consultable por id?       {proyecto_repo.buscar_por_id(proyecto_temporal.id).activo}")

    # --- 11. registro_tiempo_repo: el flujo completo, incluyendo cargar_historial ---
    separador("11. registro_tiempo_repo — por qué cargar_historial() importa")

    camila_sesion_1 = empleado_repo.buscar_por_id(camila.id)
    registro_tiempo_repo.cargar_historial(camila_sesion_1)  # aún vacío, primera vez
    r1 = camila_sesion_1.registrar_horas(date(2025, 3, 3), 6, "Terreno inicial", proyecto)
    registro_tiempo_repo.crear(r1)
    print(f"Registro creado -> id: {r1.id}, {r1.horas_trabajadas}h el {r1.fecha}")

    print("\nSimulando cerrar y reabrir el programa (nuevo objeto Empleado desde la BD):")
    camila_sesion_2 = empleado_repo.buscar_por_id(camila.id)
    print(f"  Registros en memoria antes de cargar_historial: {len(camila_sesion_2.registros_tiempo)}")
    registro_tiempo_repo.cargar_historial(camila_sesion_2)
    print(f"  Registros en memoria después de cargar_historial: {len(camila_sesion_2.registros_tiempo)}")

    print("\nProbando que el tope diario SIGUE funcionando tras recargar (debería rechazar, 6+5=11h):")
    try:
        camila_sesion_2.registrar_horas(date(2025, 3, 3), 5, "Horas extra el mismo dia", proyecto)
    except ValueError as e:
        print(f"  Rechazado correctamente -> {e}")

    r2 = camila_sesion_2.registrar_horas(date(2025, 3, 4), 4, "Terreno dia 2", proyecto)
    registro_tiempo_repo.crear(r2)

    print("\nActualizando horas del primer registro...")
    r1.horas_trabajadas = 7
    registro_tiempo_repo.actualizar(r1)
    print(f"  Tras releer: {registro_tiempo_repo.buscar_por_id(r1.id).horas_trabajadas}h")

    print(f"\nRegistros de Camila (listar_por_empleado): {len(registro_tiempo_repo.listar_por_empleado(camila.id))}")
    print(f"Registros del proyecto (listar_por_proyecto): {len(registro_tiempo_repo.listar_por_proyecto(proyecto.id))}")

    # --- 12. Limpieza final (orden importa por las FK) ---
    separador("12. Limpiando datos de prueba")
    registro_tiempo_repo.eliminar(r1.id)
    registro_tiempo_repo.eliminar(r2.id)
    departamento_repo.eliminar(depto.id)      # antes que los empleados: gerente_id es RESTRICT
    empleado_repo.eliminar(camila.id)
    empleado_repo.eliminar(pedro.id)
    assert empleado_repo.buscar_por_id(camila.id) is None
    assert empleado_repo.buscar_por_id(pedro.id) is None
    print("Todo limpio.")


if __name__ == "__main__":
    main()