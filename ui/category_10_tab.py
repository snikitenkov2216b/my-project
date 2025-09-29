# ui/category_10_tab.py - Виджет вкладки для расчетов по КатегоGрии 10.
# Реализует интерфейс для ввода данных по производству аммиака.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_10 import Category10Calculator

class Category10Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 10 "Производство аммиака".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category10Calculator(self.data_service)
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        # 1. Выбор сырья (топлива)
        self.feedstock_combobox = QComboBox()
        # Сырьем могут выступать различные виды топлива
        feedstock_list = self.data_service.get_fuels_table_1_1()
        self.feedstock_combobox.addItems(feedstock_list)
        self.feedstock_combobox.currentIndexChanged.connect(self._update_units)
        form_layout.addRow("Вид углеродсодержащего сырья:", self.feedstock_combobox)
        
        # 2. Поле для ввода расхода сырья
        consumption_layout = QHBoxLayout()
        self.feedstock_consumption_input = QLineEdit()
        consumption_validator = QDoubleValidator(0.0, 1e9, 6, self)
        consumption_validator.setLocale(self.c_locale)
        self.feedstock_consumption_input.setValidator(consumption_validator)
        
        self.units_label = QLabel()
        consumption_layout.addWidget(self.feedstock_consumption_input)
        consumption_layout.addWidget(self.units_label)
        form_layout.addRow("Расход сырья:", consumption_layout)
        
        # 3. Поле для ввода уловленного CO2
        self.recovered_co2_input = QLineEdit("0.0")
        recovered_validator = QDoubleValidator(0.0, 1e9, 6, self)
        recovered_validator.setLocale(self.c_locale)
        self.recovered_co2_input.setValidator(recovered_validator)
        form_layout.addRow("Масса уловленного CO2 (т):", self.recovered_co2_input)

        main_layout.addLayout(form_layout)
        
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Инициализируем единицы измерения для первого элемента в списке
        self._update_units()

    def _update_units(self):
        """Обновляет текст с единицами измерения в зависимости от выбранного сырья."""
        selected_feedstock = self.feedstock_combobox.currentText()
        feedstock_data = self.data_service.get_fuel_data_table_1_1(selected_feedstock)
        if feedstock_data and 'unit' in feedstock_data:
            self.units_label.setText(f"({feedstock_data['unit']})")
        else:
            self.units_label.setText("")

    def _perform_calculation(self):
        """Выполняет расчет на основе введенных данных."""
        try:
            feedstock_name = self.feedstock_combobox.currentText()
            
            consumption_str = self.feedstock_consumption_input.text().replace(',', '.')
            recovered_co2_str = self.recovered_co2_input.text().replace(',', '.')
            
            if not consumption_str:
                raise ValueError("Введите расход сырья.")
            
            consumption = float(consumption_str)
            recovered_co2 = float(recovered_co2_str) if recovered_co2_str else 0.0

            co2_emissions = self.calculator.calculate_emissions(
                feedstock_name=feedstock_name,
                feedstock_consumption=consumption,
                recovered_co2=recovered_co2
            )

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")