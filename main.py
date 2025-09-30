# main.py - Главный исполняемый файл приложения.
# Отвечает за запуск и инициализацию основных компонентов.
# Комментарии на русском. Поддержка UTF-8.

import sys
from PyQt6.QtWidgets import QApplication

# Импортируем сервис данных и главное окно
from data_models import DataService
from ui.main_window import MainWindow

def main():
    """
    Основная функция для запуска приложения.
    """
    # Создаем экземпляр приложения
    app = QApplication(sys.argv)

    # 1. Инициализируем сервис данных.
    # Он будет создан один раз и передан во все части приложения,
    # которые нуждаются в доступе к таблицам с коэффициентами.
    data_service = DataService()

    # 2. Создаем главное окно, передавая ему сервис данных.
    main_window = MainWindow(data_service)

    # 3. Показываем главное окно.
    main_window.show()

    # 4. Запускаем главный цикл обработки событий.
    sys.exit(app.exec())

if __name__ == '__main__':
    main()