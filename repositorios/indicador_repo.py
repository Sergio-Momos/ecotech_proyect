from database.conexion import cursor_db


def guardar_lote(indicadores: list[dict]) -> None:
    """Inserta o actualiza una serie dentro de una sola transacción."""
    if not indicadores:
        return
    with cursor_db() as (cursor, _):
        cursor.executemany(
            """
            INSERT INTO indicadores
                (codigo, fecha, nombre, valor, unidad_medida, fuente)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                nombre = VALUES(nombre), valor = VALUES(valor),
                unidad_medida = VALUES(unidad_medida), fuente = VALUES(fuente)
            """,
            [(
                item["codigo"], item["fecha"], item["nombre"], item["valor"],
                item["unidad_medida"], item["fuente"],
            ) for item in indicadores],
        )


def listar(codigo: str = "uf", limite: int = 30) -> list[dict]:
    if not isinstance(limite, int) or isinstance(limite, bool) or limite < 1:
        raise ValueError("El límite debe ser un entero positivo.")
    with cursor_db(dictionary=True) as (cursor, _):
        cursor.execute(
            """SELECT codigo, fecha, nombre, valor, unidad_medida, fuente, actualizado_en
               FROM indicadores WHERE codigo = %s ORDER BY fecha DESC LIMIT %s""",
            (codigo, limite),
        )
        return list(cursor.fetchall())
