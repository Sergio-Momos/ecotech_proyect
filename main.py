from datetime import date

from models.empleado import Empleado
from models.departamento import Departamento
from models.proyecto import Proyecto
from models.rol import Rol
from models.usuario import Usuario
from models.seguridad import Seguridad
from models.informe import Informe
from models.usuario import Usuario
from database.conexion import probar_conexion

def separador(titulo: str) -> None:
    print("\n" + "=" * 60)
    print(titulo)
    print("=" * 60)


def main():
    # --- 1. Empleados (Persona + herencia) ---
    separador("1. Creando empleados")
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

    # --- 2. Departamento (agregación) ---
    separador("2. Departamento")
    rrhh = Departamento(id=1, nombre="RecursosHumanos", gerente=ana)
    rrhh.agregar_empleado(ana)
    rrhh.agregar_empleado(juan)
    print(f"Departamento: {rrhh.nombre} | Gerente: {rrhh.gerente.get_nombre_completo()}")
    print(f"Empleados: {[e.get_nombre_completo() for e in rrhh.empleados]}")

    # --- 3. Proyecto (asociación N:M) ---
    separador("3. Proyecto")
    proyecto_solar = Proyecto(
        id=1, nombre="PanelesSolares",
        descripcion="Instalacion de paneles solares en oficina central",
        fecha_inicio=date(2024, 1, 10),
    )
    proyecto_solar.asignar_empleado(ana)
    proyecto_solar.asignar_empleado(juan)
    print(f"Proyecto: {proyecto_solar.nombre}")
    print(f"Participantes: {[e.get_nombre_completo() for e in proyecto_solar.empleados]}")
    print(f"Proyectos de Ana (vista desde Empleado): {[p.nombre for p in ana.proyectos]}")

    # --- 4. RegistroTiempo (composición) + topes legales ---
    separador("4. Registro de horas")
    ana.registrar_horas(date(2024, 9, 2), 6, "Instalacion de paneles", proyecto_solar)
    ana.registrar_horas(date(2024, 9, 3), 8, "Configuracion de inversor", proyecto_solar)
    for r in ana.registros_tiempo:
        print(f"  {r.fecha} - {r.horas_trabajadas}h - {r.descripcion} ({r.proyecto.nombre})")

    print("\nProbando tope diario (debería rechazar):")
    try:
        ana.registrar_horas(date(2024, 9, 2), 6, "Horas extra el mismo dia", proyecto_solar)
    except ValueError as e:
        print(f"  Rechazado correctamente -> {e}")

    # --- 5. Usuario + Rol + Seguridad ---
    separador("5. Usuario, Rol y Seguridad")
    rol_rrhh = Rol.recursos_humanos()
    print(f"Rol: {rol_rrhh} | permisos: {rol_rrhh.permisos}")

    usuario_ana = Usuario(id=1, username="ana.torres", password="Clave#2024", rol=rol_rrhh) #NOSONAR
    print(usuario_ana)
    print(f"Hash guardado internamente (solo para depurar, nunca así en la app real): {usuario_ana._password}")

    print("\nVerificando login:")
    print("  Clave correcta   ->", Seguridad.verificar_password("Clave#2024", usuario_ana._password))
    print("  Clave incorrecta ->", Seguridad.verificar_password("otraClave", usuario_ana._password))

    """
    # --- 6. Informe (recibe filas ya "aplanadas", nunca objetos de dominio) ---
    separador("6. Informe")
    filas = [
        {"nombre": e.get_nombre_completo(), "rut": e.rut, "salario": e.salario}
        for e in rrhh.empleados
    ]
    informe_empleados = Informe(tipo=Informe.TIPO_EMPLEADOS)
    informe_empleados.generar_informe(filas)
    ruta_pdf = informe_empleados.exportar_pdf("informe_empleados.pdf")
    ruta_excel = informe_empleados.exportar_excel("informe_empleados.xlsx")
    print(f"Informe generado el {informe_empleados.fecha_generacion}")
    print(f"PDF   -> {ruta_pdf}")
    print(f"Excel -> {ruta_excel}")
    """
        # --- 7. crear_usuario end-to-end, incluyendo colisión de nombres ---
    separador("7. crear_usuario (Empleado -> Usuario, con colisión)")

    rol_empleado = Rol("Empleado")  # o el classmethod que hayas definido para este rol

    usuario_de_ana = ana.crear_usuario(password="ClaveAna#1", rol=rol_rrhh) #NOSONAR
    print(f"Usuario generado para Ana: {usuario_de_ana.username}")

    # Segundo "Sergio Morales" a propósito, para forzar la colisión
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
    usuario1 = sergio1.crear_usuario(password="ClaveUno#1", rol=rol_empleado) #NOSONAR
    usuario2 = sergio2.crear_usuario(password="ClaveDos#1", rol=rol_empleado) #NOSONAR
    print(f"Sergio 1 -> username: {usuario1.username}")
    print(f"Sergio 2 -> username: {usuario2.username}")
    assert usuario1.username != usuario2.username, "¡Colisión no resuelta!"
    print("Colisión resuelta correctamente: usernames distintos.")

    # --- 8. Probar conexión a la base de datos ---
    separador("8. Conexion a MySQL")
    if probar_conexion():
        print("Conexión exitosa a la base de datos.")

        # --- 9. Probar empleado_repo contra MySQL real ---
    separador("9. empleado_repo: crear, buscar, actualizar, eliminar")

    from repositorios import empleado_repo

    nuevo = Empleado(
        id=None,  # todavía no existe en la BD
        nombre="Camila Rios", direccion="Av. Siempre Viva 742",
        telefono="933333333", correo="camila.rios@ecotech.cl",
        rut="20.730.332-1",  # con puntos y guion, a propósito, para probar normalizar_rut
        salario=725450.50, fecha_inicio_contrato=date(2024, 4, 20),
    )
    print(f"Antes de crear -> id: {nuevo.id}")

    id_generado = empleado_repo.crear(nuevo)
    print(f"Después de crear -> id: {nuevo.id} (retornado: {id_generado})")
    assert nuevo.id == id_generado, "El id del objeto no quedó sincronizado."

    recuperado = empleado_repo.buscar_por_id(nuevo.id)
    print(f"Recuperado desde la BD: {recuperado}")
    print(f"  correo: {recuperado.correo} (¿coincide? {recuperado.correo == nuevo.correo})")
    print(f"  rut:    {recuperado.rut} (¿coincide? {recuperado.rut == nuevo.rut})")
    print(f"  salario: {recuperado.salario} (¿coincide? {recuperado.salario == nuevo.salario})")

    print("\nProbando RUT duplicado (debería rechazar):")
    try:
        empleado_repo.crear(Empleado(
            id=None, nombre="Otro Nombre", direccion="Otra 123",
            telefono="944444444", correo="otro@ecotech.cl",
            rut="207303321",  # mismo RUT, sin puntos ni guion esta vez
            salario=500000, fecha_inicio_contrato=date(2024, 1, 1),
        ))
    except ValueError as e:
        print(f"  Rechazado correctamente -> {e}")

    print("\nActualizando salario...")
    recuperado.salario = 800000.0
    empleado_repo.actualizar(recuperado)
    releido = empleado_repo.buscar_por_id(recuperado.id)
    print(f"  Salario tras releer desde la BD: {releido.salario} (¿coincide? {releido.salario == 800000.0})")

    print(f"\nTotal empleados en la BD: {len(empleado_repo.listar_todos())}")
    
    print("\nLimpiando datos de prueba...")
    empleado_repo.eliminar(nuevo.id)
    assert empleado_repo.buscar_por_id(nuevo.id) is None, "¡No se eliminó correctamente!"
    print("Eliminado y confirmado.")
    
if __name__ == "__main__":
    main()