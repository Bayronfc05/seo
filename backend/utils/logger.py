"""
Sistema de logging centralizado
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str,
    log_file: str = None,
    level: str = 'INFO',
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configura un logger con handlers de archivo y consola

    Args:
        name: Nombre del logger
        log_file: Ruta del archivo de log (opcional)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Tamaño máximo del archivo antes de rotar
        backup_count: Número de archivos de backup a mantener

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)

    # Si ya tiene handlers, no añadir más
    if logger.handlers:
        return logger

    # Nivel de logging
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler de archivo (si se especifica)
    if log_file:
        # Crear directorio si no existe
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Evitar propagación a loggers padres
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger existente o crea uno básico

    Args:
        name: Nombre del logger

    Returns:
        Logger
    """
    logger = logging.getLogger(name)

    # Si no tiene handlers, configurar uno básico
    if not logger.handlers:
        logger = setup_logger(name)

    return logger
