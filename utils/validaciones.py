import re
from datetime import date
from decimal import Decimal

from .constantes import PATRON_RUT

def validar_nombre_o_apellido(valor: str, campo: str) -> str:
    if not valor or not valor.isalpha():
        raise ValueError(f"{campo} debe contener solo letras, sin espacios, números ni signos.")
    return valor

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


def validar_password(valor: str, patron: str, mensaje_error: str) -> str:
    """Valida una contraseña sin alterarla antes de almacenarla o hashearla."""
    if not isinstance(valor, str):
        raise TypeError("La contraseña debe ser un texto.")
    if not valor:
        raise ValueError("La contraseña no puede estar vacía.")
    if not re.fullmatch(patron, valor):
        raise ValueError(mensaje_error)
    return valor


def normalizar_rut(rut: str) -> str:
    """Elimina puntos y guion de un RUT para validarlo uniformemente."""
    rut = validar_texto(rut, "El RUT")
    return rut.replace(".", "").replace("-", "").upper()

def validar_id(valor: int, campo: str = "El id") -> None:
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise TypeError(f"{campo} debe ser un número entero.")
    if valor <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")


def validar_horas(valor: float) -> float:
    """Valida las horas con la misma precisión que DECIMAL(4,2) en MySQL."""
    if not isinstance(valor, (int, float)) or isinstance(valor, bool):
        raise TypeError("Las horas trabajadas deben ser un número (int o float)")
    horas = Decimal(str(valor))
    if not horas.is_finite() or not 0 < horas <= 10:
        raise ValueError("Las horas deben ser finitas, mayores que 0 y no superar las 10 horas diarias.")
    if horas != horas.quantize(Decimal("0.01")):
        raise ValueError("Las horas deben tener como máximo dos decimales.")
    return float(horas)


def validar_historial_horas(fecha: date, horas: float, historial) -> None:
    """Impide duplicar días y superar las 42 horas de una semana ISO.

    El historial contiene pares (fecha, horas). Al editar, el llamador debe
    excluir el registro que está reemplazando para no contarlo dos veces.
    """
    if type(fecha) is not date:
        raise TypeError("La fecha debe ser una instancia de date")
    total = Decimal(str(validar_horas(horas)))
    semana = fecha.isocalendar()[:2]
    for fecha_previa, horas_previas in historial:
        if fecha_previa == fecha:
            raise ValueError(f"El día {fecha} ya tiene un registro de horas.")
        if fecha_previa.isocalendar()[:2] == semana:
            total += Decimal(str(horas_previas))
    if total > 42:
        raise ValueError("Con este registro se superarían las 42 horas semanales permitidas.")
