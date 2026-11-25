"""Completa los hashes de correo antes de crear su índice único.

Ejecutar desde la raíz del proyecto después de migracion_correo_hash_preparar.sql:
    python database/migracion_correo_hash_rellenar.py
"""

import hashlib
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import AES_KEY
from database.conexion import cursor_db, establecer_perfil_activo


def main() -> None:
    if not AES_KEY:
        raise SystemExit("FERNET_KEY está vacía en .env. No se modificó la base.")

    establecer_perfil_activo("rrhh")
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            "SELECT id, CAST(AES_DECRYPT(correo, %s) AS CHAR) AS correo FROM empleados",
            (AES_KEY,),
        )
        filas = cursor.fetchall()

        hashes = []
        ids_por_correo = defaultdict(list)
        for fila in filas:
            correo = (fila["correo"] or "").strip().casefold()
            if not correo:
                raise ValueError(
                    f"El empleado {fila['id']} no tiene un correo descifrable; no se modificó la base."
                )
            correo_hash = hashlib.sha256(correo.encode("utf-8")).hexdigest()
            hashes.append((correo_hash, fila["id"]))
            ids_por_correo[correo].append(fila["id"])

        duplicados = [ids for ids in ids_por_correo.values() if len(ids) > 1]
        if duplicados:
            detalle = "; ".join(", ".join(map(str, ids)) for ids in duplicados)
            raise ValueError(
                "Hay correos repetidos en los empleados con estos ID: " + detalle +
                ". Corrígelos antes de continuar; no se modificó la base."
            )

        for correo_hash, empleado_id in hashes:
            cursor.execute(
                "UPDATE empleados SET correo_hash = %s WHERE id = %s",
                (correo_hash, empleado_id),
            )

    print(f"Hashes de correo completados para {len(hashes)} empleado(s).")


if __name__ == "__main__":
    main()
