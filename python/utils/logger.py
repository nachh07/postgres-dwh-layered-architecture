"""
Utilidades para logging
"""
import logging
import sys
from pathlib import Path
from python.config.settings import LOGS_DIR, LOG_LEVEL, LOG_FORMAT


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Configura un logger con salida a consola y archivo
    
    Args:
        name: Nombre del logger
        log_file: Nombre del archivo de log (opcional)
    
    Returns:
        logging.Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (opcional)
    if log_file:
        file_path = LOGS_DIR / log_file
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Logger por defecto
default_logger = setup_logger('data_pipeline', 'pipeline.log')
