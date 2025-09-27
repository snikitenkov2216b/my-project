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
from ui.category_12_tab import Category12Tab
from ui.category_13_tab import Category13Tab
from ui.category_14_tab import Category14Tab
from ui.category_15_tab import Category15Tab
from ui.category_16_tab import Category16Tab
from ui.category_17_tab import Category17Tab
from ui.category_18_tab import Category18Tab
from ui.category_19_tab import Category19Tab
from ui.category_20_tab import Category20Tab


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
        self.tabs.addTab(Category12Tab(self.data_service), "Кат. 12: Нефтехимия")
        self.tabs.addTab(Category13Tab(self.data_service), "Кат. 13: Фтор-вещества")
        self.tabs.addTab(Category14Tab(self.data_service), "Кат. 14: Черная металлургия")
        self.tabs.addTab(Category15Tab(self.data_service), "Кат. 15: Ферросплавы")
        self.tabs.addTab(Category16Tab(self.data_service), "Кат. 16: Алюминий")
        self.tabs.addTab(Category17Tab(self.data_service), "Кат. 17: Прочие процессы")
        self.tabs.addTab(Category18Tab(self.data_service), "Кат. 18: Транспорт")
        self.tabs.addTab(Category19Tab(self.data_service), "Кат. 19: Дорожное хозяйство")
        self.tabs.addTab(Category20Tab(self.data_service), "Кат. 20: Отходы")