"""
Logger compartido del proyecto.

Provee la función `get_logger` para obtener loggers configurados
con salida a consola y opcionalmente a archivo.
"""
import logging
import sys
from pathlib import Path

from src.shared.config.settings import settings


def get_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """
    Retorna un logger configurado con handler de consola y (opcionalmente) de archivo.

    Args:
        name:     Nombre del logger (típicamente `__name__` del módulo).
        log_file: Nombre del archivo de log dentro de `logs/`. Si es None,
                  solo se escribe a consola.

    Returns:
        logging.Logger configurado y listo para usar.
    """
    logger = logging.getLogger(name)

    # Evitar duplicar handlers si el logger ya fue configurado
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.log_level, logging.INFO))

    formatter = logging.Formatter(settings.log_format)

    # ---- Console handler --------------------------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ---- File handler (opcional) -----------------------------------------
    if log_file:
        file_path: Path = settings.logs_dir / log_file
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
