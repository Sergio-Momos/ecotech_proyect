import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gui import empleados_view
from models.rol import Rol
from repositorios import registro_tiempo_repo
from utils.validaciones import validar_nombre_o_apellido


def campo(valor):
    return Mock(get=Mock(return_value=valor))


class IntegracionMatiTests(unittest.TestCase):
    def test_ti_no_adquiere_permisos_de_horas_aunque_estuvieran_guardados(self):
        rol = Rol.ti()
        for permiso in (Rol._CREAR_REGISTRO_PROPIO, Rol._LEER_REGISTROS_PROPIOS):
            rol.agregar_permiso(permiso)
            self.assertFalse(rol.tiene_permiso(permiso))
        self.assertTrue(rol.tiene_permiso(Rol._CREAR_USUARIOS))

    def test_rrhh_y_empleado_conservan_acceso_a_horas(self):
        for rol in (Rol.recursos_humanos(), Rol.empleado_estandar()):
            self.assertTrue(rol.tiene_permiso(Rol._CREAR_REGISTRO_PROPIO))
            self.assertTrue(rol.tiene_permiso(Rol._LEER_REGISTROS_PROPIOS))

    def test_ti_no_puede_insertar_horas_directamente(self):
        with patch.object(registro_tiempo_repo, 'perfil_activo', return_value='ti'), \
                patch.object(registro_tiempo_repo, 'cursor_db') as db:
            with self.assertRaises(PermissionError):
                registro_tiempo_repo.crear(Mock())
        db.assert_not_called()

    def test_otros_perfiles_pueden_persistir_horas(self):
        from tests.test_horas import registro, usuario
        for perfil, rol in (('rrhh', Rol.recursos_humanos()), ('empleado', Rol.empleado_estandar())):
            cursor = Mock(lastrowid=42)
            cursor.fetchone.return_value = {'id': 1, 'activo': True}
            cursor.fetchall.return_value = []

            @contextmanager
            def db(**kwargs):
                yield cursor, Mock()

            with patch.object(registro_tiempo_repo, 'perfil_activo', return_value=perfil), \
                    patch.object(registro_tiempo_repo, 'cursor_db', db):
                self.assertEqual(registro_tiempo_repo.crear(registro(), usuario=usuario(rol)), 42)

    def test_nombre_y_apellido_admiten_tildes_y_rechazan_entradas_invalidas(self):
        for valor in ('José', 'Muñoz'):
            self.assertEqual(validar_nombre_o_apellido(valor, 'Nombre'), valor)
        for valor in ('', 'Ana María', 'Ana1', 'Pérez!', ' Ana'):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                validar_nombre_o_apellido(valor, 'Nombre')

    def test_formulario_guarda_nombre_completo_y_rechaza_apellido_invalido(self):
        vista = SimpleNamespace(
            _empleado_existente=None, _usuario_id=1,
            _entradas={k: campo(v) for k, v in {
                'nombre': 'Ana', 'apellido': 'Torres', 'direccion': 'Calle Prueba 123',
                'telefono': '912345678', 'correo': 'ana@example.com',
                'rut': '11.111.111-1', 'salario': '650000',
            }.items()},
            _entrada_fecha=campo('2026-10-01'), _on_guardado=Mock(), destroy=Mock(),
        )
        with patch.object(empleados_view.empleado_repo, 'crear') as crear, \
                patch.object(empleados_view, 'accion'), \
                patch.object(empleados_view, 'log_error'), \
                patch.object(empleados_view.messagebox, 'showerror') as aviso:
            empleados_view.EmpleadoFormView._guardar(vista)
            aviso.assert_not_called()
            self.assertEqual(crear.call_args.args[0]._nombre, 'Ana Torres')
            vista._on_guardado.assert_called_once()
            vista.destroy.assert_called_once()

            crear.reset_mock()
            vista._entradas['apellido'] = campo('Torres1')
            empleados_view.EmpleadoFormView._guardar(vista)
            crear.assert_not_called()
            aviso.assert_called_once()


if __name__ == '__main__':
    unittest.main()
