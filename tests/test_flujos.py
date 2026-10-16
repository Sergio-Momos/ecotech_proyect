import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gui import login_view, registros_view
from app import App
from tests.test_horas import registro, usuario, LUNES
from repositorios import usuario_repo


def entrada(texto):
    campo = Mock()
    campo.get.return_value = texto
    return campo


class LoginTests(unittest.TestCase):
    def setUp(self):
        self.vista = SimpleNamespace(_entry_usuario=entrada(" usuario "),
                                     _entry_password=entrada("Clave#2026"), _app=Mock(), _btn_mostrar_password=Mock())

    def test_login_valido_inicia_una_sola_vez(self):
        cuenta = Mock()
        cuenta.verificar_password.return_value = True
        with patch.object(login_view.usuario_repo, "buscar_por_username_activo", return_value=cuenta) as buscar:
            login_view.LoginView._intentar_login(self.vista)
        buscar.assert_called_once_with("usuario")
        self.vista._app.iniciar_sesion_exitosa.assert_called_once_with(cuenta)

    def test_error_conexion_se_muestra_sin_iniciar(self):
        with patch.object(login_view.usuario_repo, "buscar_por_username_activo", side_effect=ConnectionError("Prueba")), \
                patch.object(login_view, "log_error"), patch.object(login_view.messagebox, "showerror") as aviso:
            login_view.LoginView._intentar_login(self.vista)
        aviso.assert_called_once()
        self.vista._app.iniciar_sesion_exitosa.assert_not_called()

    def test_usuario_inactivo_no_inicia(self):
        with patch.object(login_view.usuario_repo, "buscar_por_username_activo", return_value=None), \
                patch.object(login_view, "log_error"), patch.object(login_view.messagebox, "showerror"):
            login_view.LoginView._intentar_login(self.vista)
        self.vista._app.iniciar_sesion_exitosa.assert_not_called()

    def test_login_consulta_solo_usuarios_activos(self):
        from contextlib import contextmanager
        cursor = Mock()
        cursor.fetchone.return_value = None

        @contextmanager
        def db(**kwargs):
            yield cursor, Mock()

        with patch.object(usuario_repo, "cursor_db", db):
            self.assertIsNone(usuario_repo.buscar_por_username_activo("usuario"))
        sql, params = cursor.execute.call_args.args
        self.assertIn("FROM usuarios", sql)
        self.assertIn("activo = TRUE", sql)
        self.assertEqual(params, ("usuario",))

    def test_navegacion_fallida_conserva_vista_anterior(self):
        anterior = Mock()
        app = SimpleNamespace(_contenedor=Mock(), _frame_actual=anterior)
        with self.assertRaises(ValueError):
            App.navegar_a(app, Mock(side_effect=ValueError("Prueba")))
        anterior.destroy.assert_not_called()
        self.assertIs(app._frame_actual, anterior)


class FormulariosHorasTests(unittest.TestCase):
    def test_edicion_fallida_no_modifica_objeto_original(self):
        original = registro(id=1)
        vista = SimpleNamespace(
            _registro=original, _usuario=usuario(), _usuario_id=1,
            _entrada_fecha=entrada((LUNES + timedelta(days=1)).isoformat()), _entrada_horas=entrada("10"),
            _entrada_descripcion=entrada("Nueva descripcion"), _selector_proyecto=entrada("Proyecto"),
            _mapa_proyectos={"Proyecto": original._proyecto}, _on_guardado=Mock(), destroy=Mock(),
        )
        with patch.object(registros_view.registro_tiempo_repo, "actualizar", side_effect=ValueError("Semana excedida")), \
                patch.object(registros_view, "log_error"), patch.object(registros_view.messagebox, "showerror"):
            registros_view.RegistroFormView._guardar(vista)
        self.assertEqual(original._fecha, LUNES)
        self.assertEqual(original._horas_trabajadas, 8)
        self.assertEqual(original._descripcion, "Prueba")
        vista._on_guardado.assert_not_called()
        vista.destroy.assert_not_called()

    def test_lote_fallido_no_registra_exito_ni_modifica_historial(self):
        base = registro()
        vista = SimpleNamespace(
            _empleado=base._empleado, _usuario=usuario(), _usuario_id=1,
            _selector_proyecto=entrada("Proyecto"), _mapa_proyectos={"Proyecto": base._proyecto},
            _filas=[(LUNES, entrada("8"), entrada("Prueba"), False)],
            _on_guardado=Mock(), destroy=Mock(),
        )
        vista._error_bd = lambda mensaje, e: registros_view.CargaMasivaView._error_bd(vista, mensaje, e)
        with patch.object(registros_view.registro_tiempo_repo, "crear_lote", side_effect=ConnectionError("Prueba")), \
                patch.object(registros_view, "log_error"), \
                patch.object(registros_view, "registro_horas") as auditar, \
                patch.object(registros_view.messagebox, "showerror"):
            registros_view.CargaMasivaView._guardar_lote(vista)
        self.assertEqual(base._empleado._registros_tiempo, ())
        auditar.assert_not_called()
        vista._on_guardado.assert_not_called()
        vista.destroy.assert_not_called()


if __name__ == "__main__":
    unittest.main()
