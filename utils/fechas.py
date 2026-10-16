from datetime import date, datetime


def leer_fecha_opcional(texto: str, nombre: str) -> date | None:
    """Convierte una fecha de filtro; un campo vacío indica que no hay límite."""
    texto = texto.strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"La fecha '{nombre}' debe tener el formato AAAA-MM-DD.") from None
