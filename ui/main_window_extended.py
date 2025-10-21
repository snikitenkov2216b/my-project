# ui/main_window_extended.py
"""
Расширенное главное окно приложения с поддержкой расчетов поглощения ПГ.
"""
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QMenuBar, QMenu,
    QMessageBox, QVBoxLayout, QWidget, QStatusBar,
    QToolBar, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QKeySequence

# Импорт существующих вкладок выбросов
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

# Импорт новых вкладок поглощения
from ui.absorption_tabs import (
    ForestRestorationTab,
    AgriculturalAbsorptionTab
)

# Импорт расширенной фабрики калькуляторов
from calculations.calculator_factory_extended import ExtendedCalculatorFactory


class ExtendedMainWindow(QMainWindow):
    """Главное окно приложения с расширенной функциональностью."""
    
    def __init__(self):
        super().__init__()
        self.calculator_factory = ExtendedCalculatorFactory()
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        logging.info("Extended GHG Calculator application started")
    
    def _init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle("Калькулятор парниковых газов - Расширенная версия")
        self.setGeometry(100, 100, 1400, 900)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        
        # Главные вкладки (выбросы vs поглощение)
        self.main_tabs = QTabWidget()
        
        # Вкладка выбросов
        self.emissions_tabs = QTabWidget()
        self.emissions_tabs.setTabPosition(QTabWidget.TabPosition.West)
        self._init_emission_tabs()
        
        # Вкладка поглощения
        self.absorption_tabs = QTabWidget()
        self.absorption_tabs.setTabPosition(QTabWidget.TabPosition.West)
        self._init_absorption_tabs()
        
        # Добавляем главные вкладки
        self.main_tabs.addTab(self.emissions_tabs, "📊 Выбросы ПГ")
        self.main_tabs.addTab(self.absorption_tabs, "🌲 Поглощение ПГ")
        
        main_layout.addWidget(self.main_tabs)
        
    def _init_emission_tabs(self):
        """Инициализация вкладок расчета выбросов."""
        # Группируем вкладки по типам
        
        # Топливо и энергетика
        self.emissions_tabs.addTab(
            Category0Tab(self.calculator_factory.get_calculator("Category0")),
            "0️⃣ Расход ресурсов"
        )
        self.emissions_tabs.addTab(
            Category1Tab(self.calculator_factory.get_calculator("Category1")),
            "1️⃣ Стац. сжигание"
        )
        self.emissions_tabs.addTab(
            Category2Tab(self.calculator_factory.get_calculator("Category2")),
            "2️⃣ Факелы"
        )
        self.emissions_tabs.addTab(
            Category3Tab(self.calculator_factory.get_calculator("Category3")),
            "3️⃣ Фугитивные"
        )
        
        # Промышленные процессы
        self.emissions_tabs.addTab(
            Category4Tab(self.calculator_factory.get_calculator("Category4")),
            "4️⃣ Нефтепереработка"
        )
        self.emissions_tabs.addTab(
            Category5Tab(self.calculator_factory.get_calculator("Category5")),
            "5️⃣ Производство кокса"
        )
        self.emissions_tabs.addTab(
            Category6Tab(self.calculator_factory.get_calculator("Category6")),
            "6️⃣ Цемент"
        )
        self.emissions_tabs.addTab(
            Category7Tab(self.calculator_factory.get_calculator("Category7")),
            "7️⃣ Известь"
        )
        self.emissions_tabs.addTab(
            Category8Tab(self.calculator_factory.get_calculator("Category8")),
            "8️⃣ Стекло"
        )
        self.emissions_tabs.addTab(
            Category9Tab(self.calculator_factory.get_calculator("Category9")),
            "9️⃣ Керамика"
        )
        
        # Химическая промышленность
        self.emissions_tabs.addTab(
            Category10Tab(self.calculator_factory.get_calculator("Category10")),
            "🔟 Аммиак"
        )
        self.emissions_tabs.addTab(
            Category11Tab(self.calculator_factory.get_calculator("Category11")),
            "1️⃣1️⃣ Хим. N2O"
        )
        self.emissions_tabs.addTab(
            Category12Tab(self.calculator_factory.get_calculator("Category12")),
            "1️⃣2️⃣ Нефтехимия"
        )
        self.emissions_tabs.addTab(
            Category13Tab(self.calculator_factory.get_calculator("Category13")),
            "1️⃣3️⃣ Фторсодержащие"
        )
        
        # Металлургия
        self.emissions_tabs.addTab(
            Category14Tab(self.calculator_factory.get_calculator("Category14")),
            "1️⃣4️⃣ Черная металлургия"
        )
        self.emissions_tabs.addTab(
            Category15Tab(self.calculator_factory.get_calculator("Category15")),
            "1️⃣5️⃣ Ферросплавы"
        )
        self.emissions_tabs.addTab(
            Category16Tab(self.calculator_factory.get_calculator("Category16")),
            "1️⃣6️⃣ Алюминий"
        )
        self.emissions_tabs.addTab(
            Category17Tab(self.calculator_factory.get_calculator("Category17")),
            "1️⃣7️⃣ Прочие процессы"
        )
        
        # Транспорт и инфраструктура
        self.emissions_tabs.addTab(
            Category18Tab(self.calculator_factory.get_calculator("Category18")),
            "1️⃣8️⃣ Транспорт"
        )
        self.emissions_tabs.addTab(
            Category19Tab(self.calculator_factory.get_calculator("Category19")),
            "1️⃣9️⃣ Дор. хозяйство"
        )
        
        # Отходы
        self.emissions_tabs.addTab(
            Category20Tab(self.calculator_factory.get_calculator("Category20")),
            "2️⃣0️⃣ Захоронение отходов"
        )
        self.emissions_tabs.addTab(
            Category21Tab(self.calculator_factory.get_calculator("Category21")),
            "2️⃣1️⃣ Био. переработка"
        )
        self.emissions_tabs.addTab(
            Category22Tab(self.calculator_factory.get_calculator("Category22")),
            "2️⃣2️⃣ Сжигание отходов"
        )
        self.emissions_tabs.addTab(
            Category23Tab(self.calculator_factory.get_calculator("Category23")),
            "2️⃣3️⃣ Сточные воды"
        )
        self.emissions_tabs.addTab(
            Category24Tab(self.calculator_factory.get_calculator("Category24")),
            "2️⃣4️⃣ N2O из стоков"
        )
    
    def _init_absorption_tabs(self):
        """Инициализация вкладок расчета поглощения."""
        
        # Лесовосстановление и лесоразведение
        forest_restoration_calc = self.calculator_factory.get_absorption_calculator("ForestRestoration")
        self.absorption_tabs.addTab(
            ForestRestorationTab(forest_restoration_calc),
            "🌱 Лесовосстановление"
        )
        
        # Постоянные лесные земли
        permanent_forest_calc = self.calculator_factory.get_absorption_calculator("PermanentForest")
        self.absorption_tabs.addTab(
            PermanentForestTab(permanent_forest_calc),
            "🌲 Постоянные леса"
        )
        
        # Защитные насаждения
        protective_forest_calc = self.calculator_factory.get_absorption_calculator("ProtectiveForest")
        self.absorption_tabs.addTab(
            ProtectiveForestTab(protective_forest_calc),
            "🌳 Защитные насаждения"
        )
        
        # Сельскохозяйственные угодья
        agricultural_calc = self.calculator_factory.get_absorption_calculator("AgriculturalLand")
        self.absorption_tabs.addTab(
            AgriculturalAbsorptionTab(agricultural_calc),
            "🌾 Сельхозугодья"
        )
        
        # Рекультивация земель
        reclamation_calc = self.calculator_factory.get_absorption_calculator("LandReclamation")
        self.absorption_tabs.addTab(
            LandReclamationTab(reclamation_calc),
            "♻️ Рекультивация"
        )
        
        # Конверсия земель
        conversion_calc = self.calculator_factory.get_absorption_calculator("LandConversion")
        self.absorption_tabs.addTab(
            LandConversionTab(conversion_calc),
            "🔄 Конверсия земель"
        )
        
        # Сводный расчет
        self.absorption_tabs.addTab(
            AbsorptionSummaryTab(self.calculator_factory),
            "📈 Сводный расчет"
        )
    
    def _init_menu(self):
        """Инициализация меню."""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        
        new_action = QAction("Новый расчет", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_calculation)
        file_menu.addAction(new_action)
        
        open_action = QAction("Открыть проект", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("Сохранить проект", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Экспорт отчета", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_report)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Инструменты
        tools_menu = menubar.addMenu("Инструменты")
        
        balance_action = QAction("Баланс выбросов/поглощения", self)
        balance_action.triggered.connect(self._show_balance)
        tools_menu.addAction(balance_action)
        
        comparison_action = QAction("Сравнение периодов", self)
        comparison_action.triggered.connect(self._show_comparison)
        tools_menu.addAction(comparison_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction("Настройки", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)
        
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        
        docs_action = QAction("Документация", self)
        docs_action.setShortcut("F1")
        docs_action.triggered.connect(self._show_docs)
        help_menu.addAction(docs_action)
        
        methodology_action = QAction("Методология расчетов", self)
        methodology_action.triggered.connect(self._show_methodology)
        help_menu.addAction(methodology_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_toolbar(self):
        """Инициализация панели инструментов."""
        toolbar = QToolBar("Главная панель")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Кнопки быстрого доступа
        new_btn = toolbar.addAction("➕ Новый")
        new_btn.triggered.connect(self._new_calculation)
        
        open_btn = toolbar.addAction("📂 Открыть")
        open_btn.triggered.connect(self._open_project)
        
        save_btn = toolbar.addAction("💾 Сохранить")
        save_btn.triggered.connect(self._save_project)
        
        toolbar.addSeparator()
        
        emission_btn = toolbar.addAction("📊 Выбросы")
        emission_btn.triggered.connect(lambda: self.main_tabs.setCurrentIndex(0))
        
        absorption_btn = toolbar.addAction("🌲 Поглощение")
        absorption_btn.triggered.connect(lambda: self.main_tabs.setCurrentIndex(1))
        
        balance_btn = toolbar.addAction("⚖️ Баланс")
        balance_btn.triggered.connect(self._show_balance)
        
        toolbar.addSeparator()
        
        report_btn = toolbar.addAction("📄 Отчет")
        report_btn.triggered.connect(self._export_report)
        
        toolbar.addSeparator()
        
        help_btn = toolbar.addAction("❓ Справка")
        help_btn.triggered.connect(self._show_docs)
    
    def _init_statusbar(self):
        """Инициализация статусной строки."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # Метка состояния
        self.status_label = QLabel("Готово")
        self.statusbar.addWidget(self.status_label)
        
        # Прогресс-бар для длительных операций
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)
        
        # Метка с текущим режимом
        self.mode_label = QLabel("Режим: Выбросы ПГ")
        self.statusbar.addPermanentWidget(self.mode_label)
        
        # Обновление режима при переключении вкладок
        self.main_tabs.currentChanged.connect(self._update_mode_label)
    
    def _update_mode_label(self, index):
        """Обновление метки режима."""
        if index == 0:
            self.mode_label.setText("Режим: Выбросы ПГ")
        else:
            self.mode_label.setText("Режим: Поглощение ПГ")
    
    def _new_calculation(self):
        """Начать новый расчет."""
        reply = QMessageBox.question(
            self,
            "Новый расчет",
            "Начать новый расчет? Несохраненные данные будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Очистка всех полей
            logging.info("Starting new calculation")
            self.status_label.setText("Новый расчет начат")
    
    def _open_project(self):
        """Открыть сохраненный проект."""
        # TODO: Реализовать загрузку проекта
        self.status_label.setText("Открытие проекта...")
        QMessageBox.information(self, "В разработке", "Функция загрузки проекта в разработке")
    
    def _save_project(self):
        """Сохранить текущий проект."""
        # TODO: Реализовать сохранение проекта
        self.status_label.setText("Сохранение проекта...")
        QMessageBox.information(self, "В разработке", "Функция сохранения проекта в разработке")
    
    def _export_report(self):
        """Экспорт отчета."""
        # TODO: Реализовать экспорт в Excel/PDF
        self.status_label.setText("Экспорт отчета...")
        QMessageBox.information(self, "В разработке", "Функция экспорта отчета в разработке")
    
    def _show_balance(self):
        """Показать баланс выбросов и поглощения."""
        # TODO: Реализовать окно баланса
        QMessageBox.information(
            self,
            "Баланс ПГ",
            "Расчет баланса парниковых газов:\n\n"
            "Выбросы: XXX т CO2-экв\n"
            "Поглощение: YYY т CO2-экв\n"
            "Чистые выбросы: ZZZ т CO2-экв"
        )
    
    def _show_comparison(self):
        """Показать сравнение периодов."""
        QMessageBox.information(self, "В разработке", "Функция сравнения периодов в разработке")
    
    def _show_settings(self):
        """Показать настройки."""
        QMessageBox.information(self, "В разработке", "Настройки программы в разработке")
    
    def _show_docs(self):
        """Показать документацию."""
        QMessageBox.information(
            self,
            "Документация",
            "Калькулятор парниковых газов v2.0\n\n"
            "Программа реализует методики расчета:\n"
            "• Выбросов ПГ (25 категорий)\n"
            "• Поглощения ПГ (формулы 1-100)\n\n"
            "Согласно Приказу Минприроды РФ от 27.05.2022 N 371"
        )
    
    def _show_methodology(self):
        """Показать методологию расчетов."""
        QMessageBox.information(
            self,
            "Методология",
            "Методология расчетов основана на:\n\n"
            "1. Приказе Минприроды РФ от 27.05.2022 N 371\n"
            "2. Руководящих принципах МГЭИК 2006 г.\n"
            "3. Национальных коэффициентах выбросов\n\n"
            "Все формулы и коэффициенты соответствуют\n"
            "официальной методике РФ"
        )
    
    def _show_about(self):
        """Показать информацию о программе."""
        QMessageBox.about(
            self,
            "О программе",
            "Калькулятор парниковых газов v2.0\n\n"
            "Программа для расчета выбросов и поглощения\n"
            "парниковых газов согласно методике\n"
            "Минприроды России\n\n"
            "© 2024 GHG Calculator Team"
        )


# Заглушки для вкладок, которые еще не реализованы
class PermanentForestTab(QWidget):
    def __init__(self, calculator, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Расчеты для постоянных лесных земель\n(Формулы 27-59)"))


class ProtectiveForestTab(QWidget):
    def __init__(self, calculator, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Расчеты для защитных насаждений\n(Формулы 60-74)"))


class LandReclamationTab(QWidget):
    def __init__(self, calculator, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Расчеты для рекультивации земель\n(Формулы 13-26)"))


class LandConversionTab(QWidget):
    def __init__(self, calculator, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Расчеты для конверсии земель\n(Формулы 91-100)"))


class AbsorptionSummaryTab(QWidget):
    def __init__(self, factory, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Сводный расчет поглощения ПГ\nОбобщение всех расчетов"))