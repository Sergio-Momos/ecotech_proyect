# utils/auditoria.py
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_FORMATO = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
_MAX_BYTES   = 5 * 1024 * 1024  # 5 MB por archivo antes de rotar
_BACKUPS     = 3                 # mantiene los últimos 3 archivos rotados


def _crear_logger(nombre: str, archivo: str) -> logging.Logger:
    log = logging.getLogger(nombre)
    log.setLevel(logging.INFO)
    if not log.handlers:
        h = RotatingFileHandler(
            os.path.join(LOG_DIR, archivo),
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUPS,
            encoding="utf-8",
        )
        h.setFormatter(_FORMATO)
        log.addHandler(h)
    return log


_log_acciones = _crear_logger("acciones", "acciones.log")
_log_horas    = _crear_logger("horas",    "horas.log")
_log_errores  = _crear_logger("errores",  "errores.log")
_log_errores.setLevel(logging.ERROR)


# ── API pública ────────────────────────────────────────────────────────────────

def accion(usuario_id: int | str, accion: str, detalle: str = "") -> None:
    """
    Registra una acción exitosa en el sistema.
    Ejemplos de uso:
        accion(3, "CREAR_EMPLEADO",      "empleado_id=7")
        accion(3, "DESACTIVAR_EMPLEADO", "empleado_id=7")
        accion(1, "CREAR_USUARIO",       "usuario_id=7, rol=Empleado")
        accion(1, "RESETEAR_PASSWORD",   "usuario_id=7")
        accion(2, "DESACTIVAR_USUARIO",  "usuario_id=7")
        accion(5, "CREAR_DEPARTAMENTO",  "dpto_id=3")
        accion(5, "ASIGNAR_EMPLEADO_DPTO", "dpto_id=3, empleado_id=9")
        accion(5, "CREAR_PROYECTO",      "proyecto_id=2")
        accion(5, "DESACTIVAR_PROYECTO", "proyecto_id=2")
    """
    msg = f"usuario_id={usuario_id} | accion={accion}"
    if detalle:
        msg += f" | {detalle}"
    _log_acciones.info(msg)


def registro_horas(usuario_id: int | str, empleado_id: int, proyecto_id: int,
                   fecha: str, horas: float) -> None:
    """
    Registra específicamente cada carga de horas trabajadas.
        registro_horas(5, 5, 2, "2025-03-03", 6.0)
    """
    _log_horas.info(
        f"usuario_id={usuario_id} | empleado_id={empleado_id} "
        f"| proyecto_id={proyecto_id} | fecha={fecha} | horas={horas}"
    )


def error(usuario_id: int | str, accion: str, descripcion: str) -> None:
    """
    Registra un error o fallo durante una acción.
        error(5, "CREAR_EMPLEADO", "RUT duplicado")
        error(0, "LOGIN", "usuario no encontrado: jperez")
    """
    _log_errores.error(
        f"usuario_id={usuario_id} | accion={accion} | error={descripcion}"
    )