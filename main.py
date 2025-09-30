# main.py - Главный исполняемый файл приложения.
# Комментарии на русском. Поддержка UTF-8.

import sys
import logging
from PyQt6.QtWidgets import QApplication

from data_models import DataService
from ui.main_window import MainWindow
from logger_config import setup_logging


def main():
    """
    Основная функция для запуска приложения.
    """
    # 1. Настраиваем систему логирования
    setup_logging()

    try:
        logging.info("Запуск приложения...")

        # 2. Создаем экземпляр приложения Qt
        app = QApplication(sys.argv)
        logging.info("QApplication создан.")

        # 3. Инициализируем сервис данных
        data_service = DataService()
        logging.info("DataService инициализирован.")

        # 4. Создаем главное окно
        main_window = MainWindow(data_service)
        logging.info("MainWindow создан.")

        # 5. Показываем главное окно
        main_window.show()
        logging.info("Главное окно отображено.")

        # 6. Запускаем главный цикл обработки событий
        sys.exit(app.exec())

    except Exception as e:
        logging.critical(
            f"Критическая ошибка при запуске приложения: {e}", exc_info=True
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
