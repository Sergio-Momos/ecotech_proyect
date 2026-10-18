import unittest
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from mysql.connector import Error as DatabaseError

from database import conexion
from models.empleado import Empleado
from models.proyecto import Proyecto
from models.registro_tiempo import RegistroTiempo
from models.rol import Rol
from repositorios import registro_tiempo_repo as repo
from utils.validaciones import validar_historial_horas


LUNES = date.today() - timedelta(days=date.today().weekday() + 7)


def empleado(id=1):
    return Empleado(id, "Ana Torres", "Direccion de prueba", "912345678",
                    "ana@example.com", "11.111.111-1", 650000, LUNES)


def registro(dia=0, horas=8, id=None, empleado_id=1):
    proyecto = Proyecto(1, "Proyecto de prueba", "Prueba", LUNES)
    nuevo = RegistroTiempo(LUNES + timedelta(days=dia), horas, "Prueba",
                           empleado(empleado_id), proyecto)
    if id is not None:
        nuevo._id = id
    return nuevo


def usuario(rol=None, id=1):
    return SimpleNamespace(_id=id, _activo=True, _rol=rol or Rol.recursos_humanos())


def fila(id, dia=0, horas=8):
    return {"id": id, "fecha": LUNES + timedelta(days=dia),
            "horas_trabajadas": horas, "proyecto_id": 1}


class ReglasModeloTests(unittest.TestCase):
    def test_usuario_en_memoria_y_password(self):
        emp = empleado()
        cuenta = emp.crear_usuario("Ejemplo#2026", Rol.ti())
        self.assertEqual(cuenta._username, "a.torres")
        self.assertTrue(cuenta.verificar_password("Ejemplo#2026"))
        self.assertFalse(cuenta.verificar_password("Incorrecta#2026"))
        with self.assertRaises(ValueError):
            emp.crear_usuario("OtraClave#2026", Rol.ti())

    def test_limite_semanal_en_modelo(self):
        emp = empleado()
        proyecto = registro()._proyecto
        for dia in range(5):
            emp.registrar_horas(LUNES + timedelta(days=dia), 8, "Prueba", proyecto)
        with self.assertRaisesRegex(ValueError, "42 horas"):
            emp.registrar_horas(LUNES + timedelta(days=5), 3, "Prueba", proyecto)
        self.assertEqual(len(emp._registros_tiempo), 5)

    def test_numeros_invalidos_y_precision(self):
        for valor in (float("nan"), float("inf"), -1, 0, 10.01, 1.333):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                registro(horas=valor)
        self.assertEqual(registro(horas=1.25)._horas_trabajadas, 1.25)

    def test_semana_iso_entre_anos(self):
        with self.assertRaisesRegex(ValueError, "42 horas"):
            validar_historial_horas(date(2021, 1, 1), 10, [(date(2020, 12, 28), 40)])
        validar_historial_horas(date(2021, 1, 4), 10, [(date(2020, 12, 28), 40)])

    def test_limite_exacto_y_suma_decimal(self):
        validar_historial_horas(LUNES + timedelta(days=5), 1.9,
                                [(LUNES, 40.1)])
        with self.assertRaisesRegex(ValueError, "42 horas"):
            validar_historial_horas(LUNES + timedelta(days=5), 1.91,
                                    [(LUNES, 40.1)])


class PersistenciaHorasTests(unittest.TestCase):
    def setUp(self):
        self.conn = Mock()
        self.cursor = self.conn.cursor.return_value
        self.cursor.fetchone.return_value = {"id": 1, "activo": True}
        self.cursor.fetchall.return_value = []
        self.cursor.lastrowid = 10
        self.obtener = patch.object(conexion, "obtener_conexion", return_value=self.conn)
        self.obtener.start()
        self.addCleanup(self.obtener.stop)

    def test_lote_un_solo_commit(self):
        registros = [registro(0), registro(1)]
        self.cursor.lastrowid = 9

        def ejecutar(sql, params):
            if "INSERT INTO registros_tiempo" in sql:
                self.cursor.lastrowid += 1

        self.cursor.execute.side_effect = ejecutar
        self.assertEqual(repo.crear_lote(registros, usuario=usuario()), [10, 11])
        self.conn.commit.assert_called_once()
        self.conn.rollback.assert_not_called()
        self.conn.close.assert_called_once()
        self.cursor.close.assert_called_once()
        self.assertTrue(all(r._id is not None for r in registros))

    def test_lote_falla_a_mitad_y_se_puede_reintentar(self):
        registros = [registro(0), registro(1)]
        insertados = 0

        def ejecutar(sql, params):
            nonlocal insertados
            if "INSERT INTO registros_tiempo" in sql:
                insertados += 1
                if insertados == 2:
                    raise DatabaseError("Fallo simulado")

        self.cursor.execute.side_effect = ejecutar
        with self.assertRaises(DatabaseError):
            repo.crear_lote(registros, usuario=usuario())
        self.conn.commit.assert_not_called()
        self.conn.rollback.assert_called_once()
        self.assertTrue(all(r._id is None for r in registros))
        self.cursor.execute.side_effect = None
        repo.crear_lote(registros, usuario=usuario())
        self.conn.commit.assert_called_once()

    def test_fallo_commit_no_asigna_ids(self):
        nuevo = registro()
        self.conn.commit.side_effect = DatabaseError("Fallo al confirmar")
        with self.assertRaises(DatabaseError):
            repo.crear(nuevo, usuario=usuario())
        self.assertIsNone(nuevo._id)
        self.conn.rollback.assert_called_once()

    def test_lote_rechaza_dos_dias_iguales(self):
        registros = [registro(), registro()]
        with self.assertRaisesRegex(ValueError, "ya tiene"):
            repo.crear_lote(registros, usuario=usuario())
        self.conn.commit.assert_not_called()
        self.conn.rollback.assert_called_once()
        self.assertTrue(all(r._id is None for r in registros))

    def test_lote_revalida_historial_existente(self):
        self.cursor.fetchall.return_value = [fila(1, dia=0)]
        with self.assertRaisesRegex(ValueError, "ya tiene"):
            repo.crear(registro(), usuario=usuario())
        self.conn.rollback.assert_called_once()

    def test_lote_rechaza_exceso_semanal(self):
        registros = [registro(dia, 9) for dia in range(5)]
        with self.assertRaisesRegex(ValueError, "42 horas"):
            repo.crear_lote(registros, usuario=usuario())
        self.conn.commit.assert_not_called()
        self.assertTrue(all(r._id is None for r in registros))

    def test_rrhh_edita_sin_contar_el_registro_dos_veces(self):
        self.cursor.fetchall.return_value = [fila(1, horas=8)]
        repo.actualizar(registro(horas=9, id=1), usuario=usuario())
        self.conn.commit.assert_called_once()
        update = [c for c in self.cursor.execute.call_args_list if "UPDATE registros_tiempo" in c.args[0]]
        self.assertEqual(update[0].args[1][-2:], (1, 1))

    def test_ti_no_edita_registro_ajeno(self):
        with self.assertRaises(PermissionError):
            repo.actualizar(registro(id=2, empleado_id=2), usuario=usuario(Rol.ti()))
        self.conn.cursor.assert_not_called()

    def test_ti_tampoco_edita_sus_horas(self):
        with self.assertRaises(PermissionError):
            repo.actualizar(registro(id=1), usuario=usuario(Rol.ti()))
        self.conn.cursor.assert_not_called()

    def test_ti_no_carga_lotes(self):
        with self.assertRaises(PermissionError):
            repo.crear_lote([registro()], usuario=usuario(Rol.ti()))
        self.conn.cursor.assert_not_called()

    def test_no_puede_crear_horas_para_otro_empleado(self):
        with self.assertRaises(PermissionError):
            repo.crear(registro(empleado_id=2), usuario=usuario(Rol.empleado_estandar()))
        self.conn.cursor.assert_not_called()

    def test_carga_rechaza_fecha_anterior_a_30_dias(self):
        nuevo = registro()
        nuevo._fecha = date.today() - timedelta(days=31)
        with self.assertRaisesRegex(ValueError, "30 días"):
            repo.crear(nuevo, usuario=usuario())
        self.conn.cursor.assert_not_called()

    def test_no_se_puede_falsificar_el_dueno_del_registro(self):
        self.cursor.fetchall.return_value = [fila(1)]
        with self.assertRaisesRegex(ValueError, "pertenece"):
            repo.actualizar(registro(id=2), usuario=usuario())
        self.conn.commit.assert_not_called()

    def test_empleado_estandar_no_puede_editar(self):
        with self.assertRaises(PermissionError):
            repo.actualizar(registro(id=1), usuario=usuario(Rol.empleado_estandar()))

    def test_rrhh_puede_editar_registro_ajeno(self):
        self.cursor.fetchall.return_value = [fila(2)]
        repo.actualizar(registro(id=2, empleado_id=2), usuario=usuario(Rol.recursos_humanos()))
        self.conn.commit.assert_called_once()

    def test_edicion_rechaza_exceso_semanal(self):
        self.cursor.fetchall.return_value = [fila(i + 1, i, 10 if i == 1 else 8) for i in range(5)]
        with self.assertRaisesRegex(ValueError, "42 horas"):
            repo.actualizar(registro(horas=10, id=1, dia=5), usuario=usuario())
        self.conn.commit.assert_not_called()

    def test_edicion_rechaza_fecha_duplicada(self):
        self.cursor.fetchall.return_value = [fila(1, 0), fila(2, 1)]
        with self.assertRaisesRegex(ValueError, "ya tiene"):
            repo.actualizar(registro(id=1, dia=1), usuario=usuario())
        self.conn.commit.assert_not_called()

    def test_sesion_de_empleado_desactivado_no_puede_cargar(self):
        self.cursor.fetchone.return_value = {"id": 1, "activo": False}
        with self.assertRaises(PermissionError):
            repo.crear(registro(), usuario=usuario())
        self.conn.commit.assert_not_called()

    def test_ti_no_puede_borrar(self):
        with self.assertRaises(PermissionError):
            repo.eliminar(1, usuario=usuario(Rol.ti()))
        self.conn.cursor.assert_not_called()

    def test_proyecto_inactivo_no_acepta_nueva_carga(self):
        self.cursor.fetchone.side_effect = [{"id": 1, "activo": True}, None]
        with self.assertRaisesRegex(ValueError, "inactivo"):
            repo.crear(registro(), usuario=usuario())
        self.conn.commit.assert_not_called()

    def test_cursor_falla_y_la_conexion_se_cierra(self):
        self.conn.cursor.side_effect = DatabaseError("No se pudo crear cursor")
        with self.assertRaises(DatabaseError):
            with conexion.cursor_db():
                pass
        self.conn.rollback.assert_called_once()
        self.conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
