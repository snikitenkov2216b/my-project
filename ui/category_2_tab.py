# ui/category_2_tab.py - Виджет вкладки для расчетов по Категории 2.
# Этот модуль отвечает за создание пользовательского интерфейса для
# ввода данных и отображения результатов по сжиганию в факелах.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox,
    QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt

# Импортируем сервисы данных и логики
from data_models import DataService
from calculations.category_2 import Category2Calculator

class Category2Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 2 "Сжигание в факелах".
    """
    def __init__(self, data_service: DataService, parent=None):
        """
        Конструктор вкладки.
        
        :param data_service: Экземпляр сервиса для доступа к данным.
        :param parent: Родительский виджет.
        """
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category2Calculator(self.data_service)

        # Инициализация пользовательского интерфейса
        self._init_ui()

    def _init_ui(self):
        """
        Инициализирует все элементы пользовательского интерфейса на вкладке.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Форма для ввода данных ---
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 1. Выпадающий список для выбора вида газа
        self.gas_type_combobox = QComboBox()
        gas_types = self.data_service.get_flare_gas_types_table_2_1()
        self.gas_type_combobox.addItems(gas_types)
        form_layout.addRow("Вид сжигаемого газа:", self.gas_type_combobox)

        # 2. Поле для ввода расхода газа
        self.consumption_input = QLineEdit()
        self.consumption_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        self.consumption_input.setPlaceholderText("Введите числовое значение")
        form_layout.addRow("Расход газа:", self.consumption_input)

        # 3. Выпадающий список для выбора единиц измерения
        self.unit_combobox = QComboBox()
        # Таблица 2.1 предоставляет коэффициенты для массы и объема
        self.unit_combobox.addItems(["тонна", "тыс. м3"])
        form_layout.addRow("Единицы измерения:", self.unit_combobox)

        main_layout.addLayout(form_layout)

        # --- Кнопка расчета и область результатов ---
        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _perform_calculation(self):
        """
        Выполняет расчет при нажатии на кнопку.
        """
        try:
            # 1. Сбор данных из полей ввода
            gas_type = self.gas_type_combobox.currentText()
            unit = self.unit_combobox.currentText()
            
            consumption_str = self.consumption_input.text().replace(',', '.')
            if not consumption_str:
                raise ValueError("Поле 'Расход газа' не может быть пустым.")
            
            consumption = float(consumption_str)

            # 2. Вызов метода из модуля расчетов
            emissions = self.calculator.calculate_emissions(
                gas_type=gas_type,
                consumption=consumption,
                unit=unit
            )

            # 3. Отображение результата для обоих газов
            co2 = emissions.get('co2', 0.0)
            ch4 = emissions.get('ch4', 0.0)
            self.result_label.setText(f"Результат: {co2:.4f} тонн CO2, {ch4:.4f} тонн CH4")

        except ValueError as e:
            # Обработка ошибок ввода
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            # Обработка других непредвиденных ошибок
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")