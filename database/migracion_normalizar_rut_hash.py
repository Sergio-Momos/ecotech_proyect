"""Normaliza los hashes de RUT existentes para búsquedas consistentes.

Ejecutar desde la raíz del proyecto, con la base de datos configurada:
    python database/migracion_normalizar_rut_hash.py
"""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import AES_KEY
from database.conexion import cursor_db, establecer_perfil_activo
from utils.validaciones import normalizar_rut, validar_rut_chileno


def main() -> None:
    if not AES_KEY:
        raise SystemExit("FERNET_KEY está vacía en .env. No se modificó la base.")

    establecer_perfil_activo("rrhh")
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            "SELECT id, CAST(AES_DECRYPT(rut, %s) AS CHAR) AS rut FROM empleados",
            (AES_KEY,),
        )
        empleados = cursor.fetchall()

        hashes = []
        for empleado in empleados:
            rut = normalizar_rut(empleado["rut"])
            if not validar_rut_chileno(rut):
                raise ValueError(
                    f"El RUT del empleado {empleado['id']} no es válido; no se actualizaron los hashes."
                )
            rut_hash = hashlib.sha256(rut.encode("utf-8")).hexdigest()
            hashes.append((rut_hash, empleado["id"]))

        for rut_hash, empleado_id in hashes:
            cursor.execute(
                "UPDATE empleados SET rut_hash = %s WHERE id = %s",
                (rut_hash, empleado_id),
            )

    print(f"Hashes normalizados para {len(hashes)} empleado(s).")


if __name__ == "__main__":
    main()
