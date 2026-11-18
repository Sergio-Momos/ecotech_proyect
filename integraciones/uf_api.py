"""Cliente y proceso de sincronización para la serie diaria de UF."""

import json
from http.client import HTTPException
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from repositorios import indicador_repo


URL_UF = "https://indicadores.cl/api/v1/uf.json"
FUENTE_API = "indicadores.cl"
TIMEOUT_SEGUNDOS = 8


class ErrorIndicadorUF(Exception):
    """Error controlado al consultar o procesar la API de UF."""


def consultar_serie_uf() -> list[dict]:
    """Descarga y descompone los registros diarios de UF."""
    request = Request(URL_UF, headers={"User-Agent": "EcoTechRRHH/1.0"})
    try:
        with urlopen(request, timeout=TIMEOUT_SEGUNDOS) as response:
            if response.status != 200:
                raise ErrorIndicadorUF(f"La API respondió con estado HTTP {response.status}.")
            contenido = response.read()
        payload = json.loads(contenido.decode("utf-8"))
    except HTTPError as exc:
        raise ErrorIndicadorUF(f"La API respondió con estado HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError, HTTPException) as exc:
        raise ErrorIndicadorUF(f"No se pudo conectar con la API de UF: {exc}.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ErrorIndicadorUF("La API devolvió una respuesta que no es JSON válido.") from exc

    if not isinstance(payload, dict) or payload.get("indicador") != "uf":
        raise ErrorIndicadorUF("La respuesta no contiene la serie esperada de UF.")
    nombre = payload.get("nombre")
    unidad = payload.get("unidad")
    serie = payload.get("serie")
    if not isinstance(nombre, str) or not isinstance(unidad, str) or not isinstance(serie, list):
        raise ErrorIndicadorUF("La respuesta de UF tiene una estructura incompleta.")

    fuente_datos = payload.get("fuente")
    fuente_datos = fuente_datos.get("nombre") if isinstance(fuente_datos, dict) else None
    fuente = f"{FUENTE_API} / {fuente_datos}" if isinstance(fuente_datos, str) else FUENTE_API

    indicadores = []
    for punto in serie:
        if not isinstance(punto, dict) or not isinstance(punto.get("fecha"), str):
            raise ErrorIndicadorUF("La API incluyó un dato de UF con formato inválido.")
        try:
            fecha = date.fromisoformat(punto["fecha"][:10])
            valor = Decimal(str(punto["valor"]))
        except (ValueError, InvalidOperation, TypeError) as exc:
            raise ErrorIndicadorUF("La API incluyó una fecha o valor de UF inválido.") from exc
        if not valor.is_finite() or valor <= 0:
            raise ErrorIndicadorUF("La API devolvió un valor de UF fuera de rango.")
        indicadores.append({
            "codigo": "uf",
            "fecha": fecha,
            "nombre": nombre,
            "valor": valor,
            "unidad_medida": unidad,
            "fuente": fuente,
        })

    if not indicadores:
        raise ErrorIndicadorUF("La API no entregó valores de UF para guardar.")
    return indicadores


def actualizar_serie_uf() -> int:
    """Consulta la API y guarda la serie recibida en la tabla indicadores."""
    indicadores = consultar_serie_uf()
    indicador_repo.guardar_lote(indicadores)
    return len(indicadores)
