# main.py
import sys
import os
import logging

# Настройка пути проекта
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from ui.main_window_extended import ExtendedMainWindow
from paths import LOG_FILE

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ],
)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GHG Calculator Extended")
    app.setOrganizationName("GHG Team")

    # Используем расширенное главное окно
    window = ExtendedMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
