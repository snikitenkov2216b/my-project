# ui/main_window.py - Главное окно приложения.
# Этот модуль определяет основной каркас GUI, включая виджет с вкладками
# для размещения интерфейсов различных категорий расчетов.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget

# Импортируем сервис данных и все виджеты-вкладки
from data_models import DataService
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
from ui.category_12_tab import Category12Tab # <-- ДОБАВЛЕН ИМПОРТ

class MainWindow(QMainWindow):
    """
    Главное окно приложения.
    Служит контейнером для всех виджетов-вкладок, каждая из которых
    отвечает за свою категорию расчетов.
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Калькулятор выбросов парниковых газов")
        self.resize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Добавление вкладок с сокращенными названиями для компактности
        self.tabs.addTab(Category1Tab(self.data_service), "Кат. 1: Стац. сжигание")
        self.tabs.addTab(Category2Tab(self.data_service), "Кат. 2: Сжигание в факелах")
        self.tabs.addTab(Category3Tab(self.data_service), "Кат. 3: Фугитивные выбросы")
        self.tabs.addTab(Category4Tab(self.data_service), "Кат. 4: Нефтепереработка")
        self.tabs.addTab(Category5Tab(self.data_service), "Кат. 5: Производство кокса")
        self.tabs.addTab(Category6Tab(self.data_service), "Кат. 6: Производство цемента")
        self.tabs.addTab(Category7Tab(self.data_service), "Кат. 7: Производство извести")
        self.tabs.addTab(Category8Tab(self.data_service), "Кат. 8: Производство стекла")
        self.tabs.addTab(Category9Tab(self.data_service), "Кат. 9: Производство керамики")
        self.tabs.addTab(Category10Tab(self.data_service), "Кат. 10: Производство аммиака")
        self.tabs.addTab(Category11Tab(self.data_service), "Кат. 11: Хим. пром. (N2O)")
        
        # Вкладка для Категории 12 <-- ДОБАВЛЕН НОВЫЙ БЛОК
        self.tabs.addTab(Category12Tab(self.data_service), "Кат. 12: Нефтехимия")