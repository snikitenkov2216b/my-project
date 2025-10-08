# paths.py
"""
Централизованное управление путями к файлам приложения.
Комментарии на русском. Поддержка UTF-8.
"""
from pathlib import Path
import sys

# Определяем корневую директорию проекта
if getattr(sys, 'frozen', False):
    # Если приложение скомпилировано (PyInstaller)
    BASE_DIR = Path(sys.executable).parent
else:
    # Если запуск из исходников
    BASE_DIR = Path(__file__).parent

# Директория для пользовательских данных
USER_DATA_DIR = Path.home() / ".ghg_calculator"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Основные файлы приложения
LIBRARY_FILE = USER_DATA_DIR / "formulas_library.json"
LOG_FILE = USER_DATA_DIR / "ghg_calculator.log"
CONFIG_FILE = USER_DATA_DIR / "config.json"

# Директория для экспорта (на будущее)
EXPORT_DIR = USER_DATA_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Директория для проектов (на будущее)
PROJECTS_DIR = USER_DATA_DIR / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

print(f"[INFO] Пользовательские данные: {USER_DATA_DIR}")
print(f"[INFO] Файл библиотеки формул: {LIBRARY_FILE}")
print(f"[INFO] Файл логов: {LOG_FILE}")