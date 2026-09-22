from utils.validaciones import validar_texto


class Rol:
    """Conjunto de permisos que determina qué acciones puede realizar un usuario.

    Los permisos se representan con cadenas para que el modelo no dependa de
    la interfaz. Por ejemplo, un rol de RR. HH. puede administrar empleados
    sin que esa lógica quede ligada al nombre del rol.
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

    PERMISOS_RRHH = frozenset(
        {
            CREAR_EMPLEADOS,
            ELIMINAR_EMPLEADOS,
            ASIGNAR_EMPLEADOS_DEPARTAMENTO,
            ASIGNAR_EMPLEADOS_PROYECTO,
            LEER_REGISTROS_TODOS,
            ACTUALIZAR_REGISTROS,
            ELIMINAR_REGISTROS,
        }
    )

    PERMISOS_EMPLEADO = frozenset(
        {
            CREAR_REGISTRO_PROPIO,
            LEER_REGISTROS_PROPIOS,
        }
    )

    def __init__(self, nombre: str, permisos=None) -> None:
        self.nombre = nombre
        self._permisos = set()

        if permisos is not None:
            for permiso in permisos:
                self.agregar_permiso(permiso)

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = validar_texto(valor, "El nombre del rol")

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
        return cls("Recursos Humanos", cls.PERMISOS_RRHH)

    @classmethod
    def empleado_estandar(cls) -> "Rol":
        """Crea el rol base: solo puede crear y leer sus propios registros de horas."""
        return cls("Empleado", cls.PERMISOS_EMPLEADO)

    def __str__(self) -> str:
        return self.nombre
