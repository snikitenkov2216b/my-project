# main.py
import sys
import logging
from PyQt6.QtWidgets import QApplication
from ui.main_window_extended import ExtendedMainWindow  # Используем расширенное окно
from paths import LOG_FILE

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
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