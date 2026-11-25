"""Restaura los campos cifrados de los cinco empleados demo con la clave actual.

Ejecutar desde la raíz del proyecto después de configurar FERNET_KEY en .env:
    python database/recifrar_empleados_demo.py

No elimina filas ni modifica cuentas, horas, proyectos o asignaciones.
"""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.conexion import cursor_db, establecer_perfil_activo
from config import AES_KEY


EMPLEADOS_DEMO = (
    ("Admin Principal", "Oficina Central 1", "900000001", "admin@ecotech.cl",
     "21.456.789-K", 900000),
    ("Soporte TI", "Oficina Central 2", "900000002", "ti@ecotech.cl",
     "20.333.444-3", 800000),
    ("Ana Torres", "Los Alerces 123", "912345678", "ana.torres@ecotech.cl",
     "11.111.111-1", 650000),
    ("Juan Perez", "Neptuno 097", "987654321", "juan.perez@ecotech.cl",
     "22.222.222-2", 580000),
    ("Camila Rios", "Av. Siempre Viva 742", "933333333", "camila.rios@ecotech.cl",
     "18.765.432-7", 725450),
)


def main() -> None:
    if not AES_KEY:
        raise SystemExit("FERNET_KEY está vacía en .env. No se modificó la base.")

    establecer_perfil_activo("rrhh")
    nombres_esperados = {fila[0] for fila in EMPLEADOS_DEMO}
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute("SELECT nombre FROM empleados ORDER BY nombre")
        nombres_actuales = [fila["nombre"] for fila in cursor.fetchall()]
        if len(nombres_actuales) != len(EMPLEADOS_DEMO) or set(nombres_actuales) != nombres_esperados:
            raise SystemExit(
                "La base no contiene exactamente los cinco empleados demo esperados. "
                "No se modificó ningún dato."
            )

        for nombre, direccion, telefono, correo, rut, salario in EMPLEADOS_DEMO:
            correo_normalizado = correo.strip().casefold()
            correo_hash = hashlib.sha256(correo_normalizado.encode("utf-8")).hexdigest()
            rut_normalizado = rut.replace(".", "").replace("-", "").upper()
            rut_hash = hashlib.sha256(rut_normalizado.encode("utf-8")).hexdigest()
            cursor.execute(
                """UPDATE empleados
                   SET direccion = AES_ENCRYPT(%s, %s),
                       telefono = AES_ENCRYPT(%s, %s),
                       correo = AES_ENCRYPT(%s, %s),
                       correo_hash = %s,
                       rut = AES_ENCRYPT(%s, %s),
                       rut_hash = %s,
                       salario = AES_ENCRYPT(%s, %s)
                   WHERE nombre = %s""",
                (direccion, AES_KEY, telefono, AES_KEY, correo, AES_KEY,
                 correo_hash, rut, AES_KEY, rut_hash, str(salario * 100), AES_KEY, nombre),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(f"No se pudo actualizar exactamente una fila para {nombre}.")

    print("Campos cifrados restaurados para los cinco empleados de demostración.")
    print("Se conservaron las cuentas, horas, departamentos, proyectos y asignaciones.")


if __name__ == "__main__":
    main()
