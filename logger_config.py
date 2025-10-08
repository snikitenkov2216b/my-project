# logger_config.py - Настройка системы логирования.
# Обновлен для использования централизованных путей.
# Комментарии на русском. Поддержка UTF-8.

import logging
from pathlib import Path

# Импортируем путь к файлу логов
try:
    from paths import LOG_FILE
except ImportError:
    # Fallback на случай, если paths.py недоступен
    LOG_FILE = Path.home() / ".ghg_calculator" / "ghg_calculator.log"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def setup_logging():
    """
    Настраивает систему логирования для приложения.

    - Логи записываются в файл и выводятся в консоль
    - Формат: дата-время - уровень - сообщение
    - Уровень по умолчанию: INFO
    """
    try:
        # Формат логов
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"

        # Настройка базового конфигуратора
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[
                # Запись в файл с ротацией (UTF-8 кодировка)
                logging.FileHandler(str(LOG_FILE), mode="a", encoding="utf-8"),
                # Вывод в консоль
                logging.StreamHandler(),
            ],
        )

        logging.info("=" * 60)
        logging.info("Система логирования инициализирована.")
        logging.info(f"Файл логов: {LOG_FILE}")
        logging.info("=" * 60)

    except PermissionError as e:
        print(f"[ОШИБКА] Нет прав для записи логов в {LOG_FILE}: {e}")
        print("[ОШИБКА] Логирование будет производиться только в консоль.")

        # Настройка только консольного логирования
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[logging.StreamHandler()],
        )

    except Exception as e:
        print(f"[КРИТИЧЕСКАЯ ОШИБКА] Не удалось настроить логирование: {e}")
        # Минимальная настройка
        logging.basicConfig(level=logging.INFO)
