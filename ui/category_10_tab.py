# ui/category_10_tab.py - Виджет вкладки для расчетов по Категории 10.
# Код обновлен для приема калькулятора, добавления подсказок и логирования.
# Комментарии на русском. Поддержка UTF-8.

import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QHBoxLayout,
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_10 import Category10Calculator


class Category10Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 10 "Производство аммиака".
    """

    def __init__(self, calculator: Category10Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout = QFormLayout()

        self.feedstock_combobox = QComboBox()
        feedstock_list = self.calculator.data_service.get_fuels_table_1_1()
        self.feedstock_combobox.addItems(feedstock_list)
        self.feedstock_combobox.currentIndexChanged.connect(self._update_units)
        self.feedstock_combobox.setToolTip(
            "Выберите вид сырья (например, природный газ), используемого в процессе."
        )
        form_layout.addRow("Вид углеродсодержащего сырья:", self.feedstock_combobox)

        consumption_layout = QHBoxLayout()
        self.feedstock_consumption_input = QLineEdit()
        consumption_validator = QDoubleValidator(0.0, 1e9, 6, self)
        consumption_validator.setLocale(self.c_locale)
        self.feedstock_consumption_input.setValidator(consumption_validator)
        self.feedstock_consumption_input.setToolTip(
            "Годовой расход сырья для производства аммиака."
        )

        self.units_label = QLabel()
        consumption_layout.addWidget(self.feedstock_consumption_input)
        consumption_layout.addWidget(self.units_label)
        form_layout.addRow("Расход сырья:", consumption_layout)

        self.recovered_co2_input = QLineEdit("0.0")
        recovered_validator = QDoubleValidator(0.0, 1e9, 6, self)
        recovered_validator.setLocale(self.c_locale)
        self.recovered_co2_input.setValidator(recovered_validator)
        self.recovered_co2_input.setToolTip(
            "Масса CO2, уловленного и направленного на дальнейшее использование (например, производство карбамида)."
        )
        form_layout.addRow("Масса уловленного CO2 (т):", self.recovered_co2_input)

        main_layout.addLayout(form_layout)

        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(
            self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self._update_units()

    def _update_units(self):
        """Обновляет текст с единицами измерения в зависимости от выбранного сырья."""
        selected_feedstock = self.feedstock_combobox.currentText()
        feedstock_data = self.calculator.data_service.get_fuel_data_table_1_1(
            selected_feedstock
        )
        unit_text = f"({feedstock_data.get('unit', '')})" if feedstock_data else ""
        self.units_label.setText(unit_text)

    def _get_float(self, line_edit, field_name):
        """Вспомогательная функция для получения числового значения из поля ввода."""
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        """Выполняет расчет на основе введенных данных."""
        try:
            feedstock_name = self.feedstock_combobox.currentText()
            consumption = self._get_float(
                self.feedstock_consumption_input, "Расход сырья"
            )
            recovered_co2 = self._get_float(
                self.recovered_co2_input, "Масса уловленного CO2"
            )

            co2_emissions = self.calculator.calculate_emissions(
                feedstock_name=feedstock_name,
                feedstock_consumption=consumption,
                recovered_co2=recovered_co2,
            )

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")
            logging.info(f"Category 10 calculation successful: CO2={co2_emissions}")

        except ValueError as e:
            logging.error(f"Category 10 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 10 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(
                self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}"
            )
            self.result_label.setText("Результат: Ошибка")
