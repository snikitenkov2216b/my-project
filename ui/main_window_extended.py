# ui/main_window_extended.py
"""
Расширенное главное окно приложения с поддержкой расчетов поглощения ПГ.
Оптимизированная версия с ленивой загрузкой вкладок.
"""
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QMenuBar, QMenu,
    QMessageBox, QVBoxLayout, QWidget, QStatusBar,
    QToolBar, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QKeySequence

# Импорт конфигурации для динамической загрузки вкладок
from ui.tab_config import (
    EMISSION_TABS_CONFIG,
    ABSORPTION_TABS_CONFIG,
    get_emission_tab_class,
    get_absorption_tab_class
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
        """
        Инициализация вкладок расчета выбросов.
        Использует динамическую загрузку из tab_config.py
        """
        for category_num, tab_title in EMISSION_TABS_CONFIG:
            try:
                # Динамически загружаем класс вкладки
                tab_class = get_emission_tab_class(category_num)
                if tab_class:
                    # Получаем калькулятор
                    calculator = self.calculator_factory.get_calculator(f"Category{category_num}")
                    if calculator:
                        # Создаем и добавляем вкладку
                        tab_widget = tab_class(calculator)
                        self.emissions_tabs.addTab(tab_widget, tab_title)
                    else:
                        logging.warning(f"Калькулятор для Category{category_num} не найден")
                else:
                    logging.warning(f"Класс вкладки для Category{category_num} не найден")
            except Exception as e:
                logging.error(f"Ошибка при создании вкладки Category{category_num}: {e}", exc_info=True)


    def _init_absorption_tabs(self):
        """
        Инициализация вкладок расчета поглощения.
        Использует динамическую загрузку из tab_config.py
        """
        # Получаем сервис данных один раз
        extended_data_service = self.calculator_factory.get_extended_data_service()

        for calc_type, tab_title, module_name, class_name in ABSORPTION_TABS_CONFIG:
            try:
                # Динамически загружаем класс вкладки
                tab_class = get_absorption_tab_class(module_name, class_name)
                if tab_class:
                    # Получаем калькулятор
                    calculator = self.calculator_factory.get_absorption_calculator(calc_type)
                    if calculator:
                        # Создаем вкладку (некоторым нужен extended_data_service)
                        try:
                            # Пробуем создать с сервисом данных
                            tab_widget = tab_class(calculator, extended_data_service)
                        except TypeError:
                            # Если не требуется сервис данных
                            tab_widget = tab_class(calculator)

                        self.absorption_tabs.addTab(tab_widget, tab_title)
                    else:
                        logging.warning(f"Калькулятор для {calc_type} не найден")
                else:
                    logging.warning(f"Класс вкладки {class_name} из {module_name} не найден")
            except Exception as e:
                logging.error(f"Ошибка при создании вкладки {calc_type}: {e}", exc_info=True)

        # Добавляем сводную вкладку (требует всю фабрику и ссылку на tabs)
        try:
            summary_class = get_absorption_tab_class("ui.absorption_tabs", "AbsorptionSummaryTab")
            if summary_class:
                summary_tab = summary_class(self.calculator_factory, self.absorption_tabs)
                self.absorption_tabs.addTab(summary_tab, "📈 Сводный расчет")
        except Exception as e:
            logging.error(f"Ошибка при создании сводной вкладки: {e}", exc_info=True)

    # --- Остальные методы (_init_menu, _init_toolbar, _init_statusbar и т.д.) остаются БЕЗ ИЗМЕНЕНИЙ ---
    # (Скопируйте их из предыдущего ответа, если нужно)
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
            # FIX: Реализована очистка всех полей
            self._clear_all_fields()
            logging.info("Starting new calculation")
            self.status_label.setText("Новый расчет начат")

    def _clear_all_fields(self):
        """Очистка всех полей ввода во всех вкладках."""
        # Очистка вкладок выбросов
        for i in range(self.emissions_tabs.count()):
            tab = self.emissions_tabs.widget(i)
            if hasattr(tab, 'clear_fields'):
                tab.clear_fields()
        # Очистка вкладок поглощения
        for i in range(self.absorption_tabs.count()):
            tab = self.absorption_tabs.widget(i)
            if hasattr(tab, 'clear_fields'):
                tab.clear_fields()
        logging.info("All fields cleared")

    def _open_project(self):
        """Открыть сохраненный проект."""
        self.status_label.setText("Открытие проекта...")
        QMessageBox.information(self, "В разработке", "Функция загрузки проекта в разработке")

    def _save_project(self):
        """Сохранить текущий проект."""
        self.status_label.setText("Сохранение проекта...")
        QMessageBox.information(self, "В разработке", "Функция сохранения проекта в разработке")

    def _export_report(self):
        """Экспорт отчета."""
        self.status_label.setText("Экспорт отчета...")
        QMessageBox.information(self, "В разработке", "Функция экспорта отчета в разработке")

    def _show_balance(self):
        """Показать баланс выбросов и поглощения."""
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