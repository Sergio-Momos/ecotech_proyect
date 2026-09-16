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
    CAMPO_PERMISO = "El permiso"

    PERMISOS_RRHH = frozenset(
        {
            CREAR_EMPLEADOS,
            ELIMINAR_EMPLEADOS,
            ASIGNAR_EMPLEADOS_DEPARTAMENTO,
            ASIGNAR_EMPLEADOS_PROYECTO,
        }
    )

    def __init__(self, nombre: str, permisos=None) -> None:
        self.nombre = nombre
        self._permisos = set()

        if permisos is not None:
            for permiso in permisos:
                self.agregar_permiso(permiso)

    @staticmethod
    def _validar_texto(valor: str, campo: str) -> str:
        if not isinstance(valor, str):
            raise TypeError(f"{campo} debe ser un texto.")

        valor = valor.strip()
        if not valor:
            raise ValueError(f"{campo} no puede estar vacío.")
        return valor

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = self._validar_texto(valor, "El nombre del rol")

    @property
    def permisos(self) -> frozenset[str]:
        """Permisos de solo lectura para evitar modificaciones accidentales."""
        return frozenset(self._permisos)

    def agregar_permiso(self, permiso: str) -> None:
        self._permisos.add(self._validar_texto(permiso, self.CAMPO_PERMISO))

    def quitar_permiso(self, permiso: str) -> None:
        self._permisos.discard(self._validar_texto(permiso, self.CAMPO_PERMISO))

    def tiene_permiso(self, permiso: str) -> bool:
        """Indica si el rol permite ejecutar una acción específica."""
        permiso = self._validar_texto(permiso, self.CAMPO_PERMISO)
        return permiso in self._permisos

    @classmethod
    def recursos_humanos(cls) -> "Rol":
        """Crea el rol con las facultades de administración de empleados."""
        return cls("Recursos Humanos", cls.PERMISOS_RRHH)

    def __str__(self) -> str:
        return self.nombre
