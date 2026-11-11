import unittest
from datetime import date
from unittest.mock import patch

import main


class MainTests(unittest.TestCase):
    def test_sembrar_empleados_reconoce_ti_por_rut_aunque_no_aparezca_en_lista(self):
        soporte_ti = type("EmpleadoPrueba", (), {"_id": 2, "_nombre": "Soporte TI"})()

        def buscar_por_rut(rut):
            return soporte_ti if rut == "20.333.444-3" else None

        def crear(empleado):
            empleado._id = 100
            return empleado._id

        with patch.object(main.empleado_repo, "listar_todos", return_value=[]), \
                patch.object(main.empleado_repo, "buscar_por_rut", side_effect=buscar_por_rut) as buscar, \
                patch.object(main.empleado_repo, "crear", side_effect=crear) as crear_empleado:
            empleados = main.sembrar_empleados({})

        self.assertEqual(empleados["Soporte TI"][0], soporte_ti)
        self.assertEqual(crear_empleado.call_count, 4)
        buscar.assert_any_call("20.333.444-3")

    def test_sembrar_proyecto_crea_proyecto_con_fecha_valida_y_asigna_empleados(self):
        ana = type("EmpleadoPrueba", (), {"_id": 11})()
        camila = type("EmpleadoPrueba", (), {"_id": 12})()
        empleados_roles = {
            "Ana Torres": (ana, "empleado"),
            "Camila Rios": (camila, "empleado"),
        }

        with patch.object(main.proyecto_repo, "listar_todos", return_value=[]), \
                patch.object(main.proyecto_repo, "crear", side_effect=lambda p: setattr(p, "_id", 7)) as crear, \
                patch.object(main.proyecto_repo, "asignar_empleado") as asignar:
            main.sembrar_proyecto(empleados_roles)

        proyecto = crear.call_args.args[0]
        self.assertEqual(proyecto._nombre, "PanelesSolares")
        self.assertEqual(proyecto._fecha_inicio, date.today())
        self.assertEqual(asignar.call_args_list[0].args, (7, 11))
        self.assertEqual(asignar.call_args_list[1].args, (7, 12))

    def test_sembrar_proyecto_existente_no_lo_duplica(self):
        existente = type("ProyectoPrueba", (), {"_nombre": "PanelesSolares"})()
        with patch.object(main.proyecto_repo, "listar_todos", return_value=[existente]), \
                patch.object(main.proyecto_repo, "crear") as crear:
            main.sembrar_proyecto({})
        crear.assert_not_called()


if __name__ == "__main__":
    unittest.main()
