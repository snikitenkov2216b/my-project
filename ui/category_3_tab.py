# ui/category_3_tab.py - Виджет вкладки для расчетов по Категории 3.
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

from calculations.category_3 import Category3Calculator


class Category3Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 3 "Фугитивные выбросы".
    """

    def __init__(self, calculator: Category3Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout = QFormLayout()

        self.gas_type_combobox = QComboBox()
        gas_types = self.calculator.data_service.get_fugitive_gas_types_table_3_1()
        self.gas_type_combobox.addItems(gas_types)
        self.gas_type_combobox.setToolTip(
            "Выберите тип газа, для которого рассчитываются фугитивные выбросы (Таблица 3.1)."
        )
        form_layout.addRow("Вид углеводородной смеси:", self.gas_type_combobox)

        volume_layout = QHBoxLayout()
        self.volume_input = QLineEdit()

        volume_validator = QDoubleValidator(0.0, 1e12, 6, self)
        volume_validator.setLocale(self.c_locale)
        self.volume_input.setValidator(volume_validator)
        self.volume_input.setPlaceholderText("Введите числовое значение")
        self.volume_input.setToolTip(
            "Общий годовой объем стравливания или отведения углеводородной смеси."
        )

        volume_layout.addWidget(self.volume_input)
        volume_layout.addWidget(QLabel("(тыс. м³)"))
        form_layout.addRow("Объем отведения смеси:", volume_layout)

        main_layout.addLayout(form_layout)

        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(
            self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        try:
            gas_type = self.gas_type_combobox.currentText()
            volume = self._get_float(self.volume_input, "Объем отведения смеси")

            emissions = self.calculator.calculate_emissions(
                gas_type=gas_type, volume=volume
            )

            co2 = emissions.get("co2", 0.0)
            ch4 = emissions.get("ch4", 0.0)
            self.result_label.setText(
                f"Результат: {co2:.4f} тонн CO2, {ch4:.4f} тонн CH4"
            )
            logging.info(f"Category 3 calculation successful: CO2={co2}, CH4={ch4}")

        except ValueError as e:
            logging.error(f"Category 3 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 3 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(
                self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}"
            )
            self.result_label.setText("Результат: Ошибка")
