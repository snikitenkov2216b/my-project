# ui/main_window.py - Главное окно приложения.
# Код обновлен для использования фабрики калькуляторов.
# Комментарии на русском. Поддержка UTF-8.

import sys
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QApplication
from PyQt6.QtGui import QIcon

from data_models import DataService
from calculations.calculator_factory import CalculatorFactory # ИМПОРТ ФАБРИКИ

# Импорт всех вкладок
from ui.category_0_tab import Category0Tab
from ui.category_1_tab import Category1Tab
from ui.category_2_tab import Category2Tab
from ui.category_3_tab import Category3Tab
from ui.category_4_tab import Category4Tab
from ui.category_5_tab import Category5Tab
from ui.category_6_tab import Category6Tab
from ui.category_7_tab import Category7Tab
from ui.category_8_tab import Category8Tab
from ui.category_9_tab import Category9Tab
from ui.category_10_tab import Category10Tab
from ui.category_11_tab import Category11Tab
from ui.category_12_tab import Category12Tab
from ui.category_13_tab import Category13Tab
from ui.category_14_tab import Category14Tab
from ui.category_15_tab import Category15Tab
from ui.category_16_tab import Category16Tab
from ui.category_17_tab import Category17Tab
from ui.category_18_tab import Category18Tab
from ui.category_19_tab import Category19Tab
from ui.category_20_tab import Category20Tab
from ui.category_21_tab import Category21Tab
from ui.category_22_tab import Category22Tab
from ui.category_23_tab import Category23Tab
from ui.category_24_tab import Category24Tab

class MainWindow(QMainWindow):
    """
    Класс главного окна приложения.
    Отвечает за инициализацию и отображение всех компонентов интерфейса.
    """
    def __init__(self, data_service: DataService):
        super().__init__()
        self.data_service = data_service
        # ИЗМЕНЕНО: Создаем фабрику калькуляторов
        self.calculator_factory = CalculatorFactory(self.data_service)
        
        self.setWindowTitle("Калькулятор выбросов парниковых газов")
        self.setGeometry(100, 100, 900, 700)
        # self.setWindowIcon(QIcon('path/to/your/icon.png'))

        self._init_ui()

    def _init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # --- Добавляем все вкладки, передавая им готовый калькулятор ---
        self.tabs.addTab(Category0Tab(self.calculator_factory.get_calculator("Category0")), "Кат. 0: Расход ресурсов")
        self.tabs.addTab(Category1Tab(self.calculator_factory.get_calculator("Category1")), "Кат. 1: Стац. сжигание")
        self.tabs.addTab(Category2Tab(self.calculator_factory.get_calculator("Category2")), "Кат. 2: Факелы")
        self.tabs.addTab(Category3Tab(self.calculator_factory.get_calculator("Category3")), "Кат. 3: Фугитивные")
        self.tabs.addTab(Category4Tab(self.calculator_factory.get_calculator("Category4")), "Кат. 4: Нефтепереработка")
        self.tabs.addTab(Category5Tab(self.calculator_factory.get_calculator("Category5")), "Кат. 5: Производство кокса")
        self.tabs.addTab(Category6Tab(self.calculator_factory.get_calculator("Category6")), "Кат. 6: Производство цемента")
        self.tabs.addTab(Category7Tab(self.calculator_factory.get_calculator("Category7")), "Кат. 7: Производство извести")
        self.tabs.addTab(Category8Tab(self.calculator_factory.get_calculator("Category8")), "Кат. 8: Производство стекла")
        self.tabs.addTab(Category9Tab(self.calculator_factory.get_calculator("Category9")), "Кат. 9: Керамика")
        self.tabs.addTab(Category10Tab(self.calculator_factory.get_calculator("Category10")), "Кат. 10: Производство аммиака")
        self.tabs.addTab(Category11Tab(self.calculator_factory.get_calculator("Category11")), "Кат. 11: Хим. производство (N2O)")
        self.tabs.addTab(Category12Tab(self.calculator_factory.get_calculator("Category12")), "Кат. 12: Нефтехимия")
        self.tabs.addTab(Category13Tab(self.calculator_factory.get_calculator("Category13")), "Кат. 13: Фторсодержащие")
        self.tabs.addTab(Category14Tab(self.calculator_factory.get_calculator("Category14")), "Кат. 14: Черная металлургия")
        self.tabs.addTab(Category15Tab(self.calculator_factory.get_calculator("Category15")), "Кат. 15: Ферросплавы")
        self.tabs.addTab(Category16Tab(self.calculator_factory.get_calculator("Category16")), "Кат. 16: Алюминий")
        self.tabs.addTab(Category17Tab(self.calculator_factory.get_calculator("Category17")), "Кат. 17: Прочие процессы")
        self.tabs.addTab(Category18Tab(self.calculator_factory.get_calculator("Category18")), "Кат. 18: Транспорт")
        self.tabs.addTab(Category19Tab(self.calculator_factory.get_calculator("Category19")), "Кат. 19: Дор. хозяйство")
        self.tabs.addTab(Category20Tab(self.calculator_factory.get_calculator("Category20")), "Кат. 20: Захоронение отходов")
        self.tabs.addTab(Category21Tab(self.calculator_factory.get_calculator("Category21")), "Кат. 21: Био. переработка")
        self.tabs.addTab(Category22Tab(self.calculator_factory.get_calculator("Category22")), "Кат. 22: Сжигание отходов")
        self.tabs.addTab(Category23Tab(self.calculator_factory.get_calculator("Category23")), "Кат. 23: Сточные воды (CH4)")
        self.tabs.addTab(Category24Tab(self.calculator_factory.get_calculator("Category24")), "Кат. 24: Сточные воды (N2O)")