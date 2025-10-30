# logger_config.py - Конфигурация системы логирования.
# Комментарии на русском. Поддержка UTF-8.

import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(level=logging.WARNING):
    """
    Настраивает конфигурацию логирования для всего приложения.

    Args:
        level: Уровень логирования (по умолчанию WARNING для production)
               Используйте logging.DEBUG для разработки
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Файловый handler - всегда включен
    file_handler = RotatingFileHandler(
        "logs/ghg_calculator.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)  # В файл пишем INFO и выше
    logger.addHandler(file_handler)

    # Stream handler - только для WARNING и выше (меньше шума в консоли)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.WARNING)
    logger.addHandler(stream_handler)

    # Используем lazy evaluation для логирования
    if level <= logging.INFO:
        logging.info("Система логирования инициализирована с уровнем %s", logging.getLevelName(level))
