# ui/category_21_tab.py - Виджет вкладки для расчетов по Категории 21.
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
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_21 import Category21Calculator


class Category21Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 21 "Биологическая переработка твердых отходов".
    """

    def __init__(self, calculator: Category21Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout = QFormLayout()

        self.treatment_type_combobox = QComboBox()
        treatment_types = (
            self.calculator.data_service.get_biological_treatment_types_table_21_1()
        )
        self.treatment_type_combobox.addItems(treatment_types)
        form_layout.addRow("Тип переработки:", self.treatment_type_combobox)

        self.waste_mass_input = QLineEdit()
        waste_validator = QDoubleValidator(0.0, 1e9, 6, self)
        waste_validator.setLocale(self.c_locale)
        self.waste_mass_input.setValidator(waste_validator)
        self.waste_mass_input.setToolTip(
            "Общая масса органических отходов, поступивших на переработку за год."
        )
        form_layout.addRow("Масса отходов (тонн, сырой вес):", self.waste_mass_input)

        self.recovered_ch4_input = QLineEdit("0.0")
        recovered_validator = QDoubleValidator(0.0, 1e9, 6, self)
        recovered_validator.setLocale(self.c_locale)
        self.recovered_ch4_input.setValidator(recovered_validator)
        self.recovered_ch4_input.setToolTip(
            "Количество метана, собранного и утилизированного (например, сожженного) за год."
        )
        form_layout.addRow("Рекуперированный CH4 (тонн):", self.recovered_ch4_input)

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
            treatment_type = self.treatment_type_combobox.currentText()
            waste_mass = self._get_float(self.waste_mass_input, "Масса отходов")
            recovered_ch4 = self._get_float(
                self.recovered_ch4_input, "Рекуперированный CH4"
            )

            ch4_emissions = self.calculator.calculate_ch4_emissions(
                waste_mass, treatment_type, recovered_ch4
            )
            n2o_emissions = self.calculator.calculate_n2o_emissions(
                waste_mass, treatment_type
            )

            result_text = (
                f"Результат: {ch4_emissions:.4f} тонн CH4, {n2o_emissions:.4f} тонн N2O"
            )
            self.result_label.setText(result_text)
            logging.info(
                f"Category 21 calculation successful: CH4={ch4_emissions}, N2O={n2o_emissions}"
            )
        except ValueError as e:
            logging.error(f"Category 21 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 21 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Критическая ошибка", str(e))
            self.result_label.setText("Результат: Ошибка")
