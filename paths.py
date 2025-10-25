# paths.py
"""
Централизованное управление путями к файлам приложения.
Оптимизированная версия с ленивой инициализацией директорий.
"""
from pathlib import Path
import sys
import logging

# Определяем корневую директорию проекта
if getattr(sys, 'frozen', False):
    # Если приложение скомпилировано (PyInstaller)
    BASE_DIR = Path(sys.executable).parent
else:
    # Если запуск из исходников
    BASE_DIR = Path(__file__).parent

# Директория для пользовательских данных
USER_DATA_DIR = Path.home() / ".ghg_calculator"


def ensure_directory(path):
    """
    Создает директорию если она не существует.

    Args:
        path: Path объект директории
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Не удалось создать директорию {path}: {e}")


# Ленивая инициализация - создаем директории только при первом обращении
def get_user_data_dir():
    """Возвращает директорию пользовательских данных, создавая её при необходимости."""
    ensure_directory(USER_DATA_DIR)
    return USER_DATA_DIR


# Основные файлы приложения
LIBRARY_FILE = USER_DATA_DIR / "formulas_library.json"
LOG_FILE = USER_DATA_DIR / "ghg_calculator.log"
CONFIG_FILE = USER_DATA_DIR / "config.json"

# Директория для экспорта
EXPORT_DIR = USER_DATA_DIR / "exports"

# Директория для проектов
PROJECTS_DIR = USER_DATA_DIR / "projects"


def get_export_dir():
    """Возвращает директорию экспорта, создавая её при необходимости."""
    ensure_directory(EXPORT_DIR)
    return EXPORT_DIR


def get_projects_dir():
    """Возвращает директорию проектов, создавая её при необходимости."""
    ensure_directory(PROJECTS_DIR)
    return PROJECTS_DIR


# Инициализируем основную директорию при импорте
ensure_directory(USER_DATA_DIR)

# Информационное сообщение (только если запускается напрямую)
if __name__ == "__main__":
    print(f"[INFO] Базовая директория: {BASE_DIR}")
    print(f"[INFO] Пользовательские данные: {USER_DATA_DIR}")
    print(f"[INFO] Файл библиотеки формул: {LIBRARY_FILE}")
    print(f"[INFO] Файл логов: {LOG_FILE}")