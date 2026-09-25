from utils.validaciones import validar_texto, validar_id


class Rol:
    """Conjunto de permisos que determina qué acciones puede realizar un usuario.

    `perfil_bd` es un dato distinto de los permisos: identifica qué CUENTA
    TÉCNICA de MySQL debe usarse mientras este rol esté activo (ver
    database/conexion.py). Rol no sabe ni le importa qué credenciales tiene
    ese perfil, ni si existe de verdad — solo lo declara. La validación real
    de que el perfil exista vive en la capa de conexión, no acá.
    """
    
    CREAR_EMPLEADOS = "empleados.crear"
    ELIMINAR_EMPLEADOS = "empleados.eliminar"
    ASIGNAR_EMPLEADOS_DEPARTAMENTO = "empleados.asignar_departamento"
    ASIGNAR_EMPLEADOS_PROYECTO = "empleados.asignar_proyecto"

    CREAR_REGISTRO_PROPIO = "registros.crear_propio"
    LEER_REGISTROS_PROPIOS = "registros.leer_propios"
    LEER_REGISTROS_TODOS = "registros.leer_todos"
    ACTUALIZAR_REGISTROS = "registros.actualizar"
    ELIMINAR_REGISTROS = "registros.eliminar"

    CAMPO_PERMISO = "El permiso"
    CREAR_USUARIOS = "usuarios.crear"
    RESETEAR_PASSWORD = "usuarios.resetear_password"
    DESACTIVAR_USUARIOS = "usuarios.desactivar"

    PERMISOS_TI = frozenset({
        CREAR_USUARIOS,
        RESETEAR_PASSWORD,
        DESACTIVAR_USUARIOS,
    })

    PERMISOS_RRHH = frozenset(
        {
            CREAR_EMPLEADOS,
            ELIMINAR_EMPLEADOS,
            ASIGNAR_EMPLEADOS_DEPARTAMENTO,
            ASIGNAR_EMPLEADOS_PROYECTO,
            LEER_REGISTROS_TODOS,
            ACTUALIZAR_REGISTROS,
            ELIMINAR_REGISTROS,
            CREAR_REGISTRO_PROPIO,
            LEER_REGISTROS_PROPIOS,
        }
    )

    PERMISOS_EMPLEADO = frozenset(
        {
            CREAR_REGISTRO_PROPIO,
            LEER_REGISTROS_PROPIOS,
        }
    )

    def __init__(self, nombre: str, perfil_bd: str, permisos=None) -> None:
        self._id = None
        self.nombre = nombre
        self.perfil_bd = perfil_bd
        self._permisos = set()

        if permisos is not None:
            for permiso in permisos:
                self.agregar_permiso(permiso)

    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        if self._id is not None:
            raise AttributeError("El id ya fue asignado y no puede modificarse.")
        validar_id(valor, "El id")
        self._id = valor

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = validar_texto(valor, "El nombre del rol")

    @property
    def perfil_bd(self) -> str:
        return self._perfil_bd

    @perfil_bd.setter
    def perfil_bd(self, valor: str) -> None:
        self._perfil_bd = validar_texto(valor, "El perfil de base de datos")

    @property
    def permisos(self) -> frozenset[str]:
        """Permisos de solo lectura para evitar modificaciones accidentales."""
        return frozenset(self._permisos)

    def agregar_permiso(self, permiso: str) -> None:
        self._permisos.add(validar_texto(permiso, self.CAMPO_PERMISO))

    def quitar_permiso(self, permiso: str) -> None:
        self._permisos.discard(validar_texto(permiso, self.CAMPO_PERMISO))

    def tiene_permiso(self, permiso: str) -> bool:
        """Indica si el rol permite ejecutar una acción específica."""
        permiso = validar_texto(permiso, self.CAMPO_PERMISO)
        return permiso in self._permisos

    @classmethod
    def recursos_humanos(cls) -> "Rol":
        """Crea el rol con las facultades de administración de empleados."""
        return cls("Recursos Humanos", perfil_bd="rrhh", permisos=cls.PERMISOS_RRHH)

    @classmethod
    def empleado_estandar(cls) -> "Rol":
        """Crea el rol base: solo puede crear y leer sus propios registros de horas."""
        return cls("Empleado", perfil_bd="empleado", permisos=cls.PERMISOS_EMPLEADO)

    @classmethod
    def ti(cls) -> "Rol":
        return cls("TI", perfil_bd="ti", permisos=cls.PERMISOS_TI)

    def __str__(self) -> str:
        return self.nombre
