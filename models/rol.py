from utils.validaciones import validar_texto, validar_id


class Rol:
    """Conjunto de permisos que determina qué acciones puede realizar un usuario.

    `perfil_bd` es un dato distinto de los permisos: identifica qué CUENTA
    TÉCNICA de MySQL debe usarse mientras este rol esté activo (ver
    database/conexion.py). Rol no sabe ni le importa qué credenciales tiene
    ese perfil, ni si existe de verdad — solo lo declara. La validación real
    de que el perfil exista vive en la capa de conexión, no acá.
    """
    
    _CREAR_EMPLEADOS = "empleados.crear"
    _ELIMINAR_EMPLEADOS = "empleados.eliminar"
    _ASIGNAR_EMPLEADOS_DEPARTAMENTO = "empleados.asignar_departamento"
    _ASIGNAR_EMPLEADOS_PROYECTO = "empleados.asignar_proyecto"

    _CREAR_REGISTRO_PROPIO = "registros.crear_propio"
    _LEER_REGISTROS_PROPIOS = "registros.leer_propios"
    _LEER_REGISTROS_TODOS = "registros.leer_todos"
    _ACTUALIZAR_REGISTROS = "registros.actualizar"
    _ELIMINAR_REGISTROS = "registros.eliminar"

    _CAMPO_PERMISO = "El permiso"
    _CREAR_USUARIOS = "usuarios.crear"
    _RESETEAR_PASSWORD = "usuarios.resetear_password"
    _DESACTIVAR_USUARIOS = "usuarios.desactivar"

    _PERMISOS_TI = frozenset({
        _CREAR_USUARIOS,
        _RESETEAR_PASSWORD,
        _DESACTIVAR_USUARIOS,
    })

    _PERMISOS_RRHH = frozenset(
        {
            _CREAR_EMPLEADOS,
            _ELIMINAR_EMPLEADOS,
            _ASIGNAR_EMPLEADOS_DEPARTAMENTO,
            _ASIGNAR_EMPLEADOS_PROYECTO,
            _LEER_REGISTROS_TODOS,
            _ACTUALIZAR_REGISTROS,
            _ELIMINAR_REGISTROS,
            _CREAR_REGISTRO_PROPIO,
            _LEER_REGISTROS_PROPIOS,
        }
    )

    _PERMISOS_EMPLEADO = frozenset(
        {
            _CREAR_REGISTRO_PROPIO,
            _LEER_REGISTROS_PROPIOS,
        }
    )

    def __init__(self, nombre: str, perfil_bd: str, permisos=None) -> None:
        self._valor_id = None
        self._nombre = nombre
        self._perfil_bd = perfil_bd
        self._valor_permisos = set()

        if permisos is not None:
            for permiso in permisos:
                self.agregar_permiso(permiso)

    @property
    def _id(self) -> int | None:
        return self._valor_id

    @_id.setter
    def _id(self, valor: int) -> None:
        if self._valor_id is not None:
            raise AttributeError("El id ya fue asignado y no puede modificarse.")
        validar_id(valor, "El id")
        self._valor_id = valor

    @property
    def _nombre(self) -> str:
        return self._valor_nombre

    @_nombre.setter
    def _nombre(self, valor: str) -> None:
        self._valor_nombre = validar_texto(valor, "El nombre del rol")

    @property
    def _perfil_bd(self) -> str:
        return self._valor_perfil_bd

    @_perfil_bd.setter
    def _perfil_bd(self, valor: str) -> None:
        self._valor_perfil_bd = validar_texto(valor, "El perfil de base de datos")

    @property
    def _permisos(self) -> frozenset[str]:
        """Permisos de solo lectura para evitar modificaciones accidentales."""
        return frozenset(self._valor_permisos)

    def agregar_permiso(self, permiso: str) -> None:
        self._valor_permisos.add(validar_texto(permiso, self._CAMPO_PERMISO))

    def quitar_permiso(self, permiso: str) -> None:
        self._valor_permisos.discard(validar_texto(permiso, self._CAMPO_PERMISO))

    def tiene_permiso(self, permiso: str) -> bool:
        """Indica si el rol permite ejecutar una acción específica."""
        permiso = validar_texto(permiso, self._CAMPO_PERMISO)
        return permiso in self._valor_permisos

    @classmethod
    def recursos_humanos(cls) -> "Rol":
        """Crea el rol con las facultades de administración de empleados."""
        return cls("Recursos Humanos", perfil_bd="rrhh", permisos=cls._PERMISOS_RRHH)

    @classmethod
    def empleado_estandar(cls) -> "Rol":
        """Crea el rol base: solo puede crear y leer sus propios registros de horas."""
        return cls("Empleado", perfil_bd="empleado", permisos=cls._PERMISOS_EMPLEADO)

    @classmethod
    def ti(cls) -> "Rol":
        return cls("TI", perfil_bd="ti", permisos=cls._PERMISOS_TI)

    def __str__(self) -> str:
        return self._nombre
