import re

from .constantes import PATRON_RUT


def validar_texto(valor: str, campo: str) -> str:
    if not isinstance(valor, str):
        raise TypeError(f"{campo} debe ser un texto.")
    valor = valor.strip()
    if not valor:
        raise ValueError(f"{campo} no puede estar vacío.")
    return valor

def validar_rut_chileno(rut: str) -> bool:
    if not isinstance(rut, str) or not re.fullmatch(PATRON_RUT, rut):
        return False

    try:
        cuerpo = rut[:-1]
        digito_verificador = rut[-1].upper()
        if not cuerpo.isdigit():
            return False
        if len(cuerpo) < 7 or len(cuerpo) > 8:
            return False

        suma = sum(
            int(digito) * (i % 6 + 2)
            for i, digito in enumerate(reversed(cuerpo))
        )
        resto = 11 - (suma % 11)
        if resto == 11:
            dv_esperado = "0"
        elif resto == 10:
            dv_esperado = "K"
        else:
            dv_esperado = str(resto)
        return digito_verificador == dv_esperado
    except (ValueError, IndexError):
        return False

def validar_con_patron(valor: str, campo: str, patron: str, mensaje_error: str) -> str:
    valor = validar_texto(valor, campo)
    if not re.fullmatch(patron, valor):
        raise ValueError(mensaje_error)
    return valor


def normalizar_rut(rut: str) -> str:
    """Elimina puntos y guion de un RUT para validarlo uniformemente."""
    rut = validar_texto(rut, "El RUT")
    return rut.replace(".", "").replace("-", "").upper()
