# ui/category_8_tab.py - Виджет вкладки для расчетов по Категории 8.
# Код обновлен для приема калькулятора, добавления подсказок и логирования.
# Комментарии на русском. Поддержка UTF-8.

import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QHBoxLayout,
    QGroupBox,
    QScrollArea,
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_8 import Category8Calculator


class Category8Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 8 "Производство стекла".
    """

    def __init__(self, calculator: Category8Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.carbonate_rows = []
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        form_container_layout = QVBoxLayout(main_widget)
        form_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(main_widget)
        main_layout.addWidget(scroll_area)

        group_box = QGroupBox("Карбонатное сырье, используемое в шихте")
        self.materials_layout = QVBoxLayout(group_box)
        add_button = QPushButton("Добавить карбонат")
        add_button.clicked.connect(self._add_carbonate_row)
        self.materials_layout.addWidget(add_button)
        form_container_layout.addWidget(group_box)

        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        form_container_layout.addWidget(
            self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight
        )
        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        form_container_layout.addWidget(
            self.result_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

    def _add_carbonate_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        combo = QComboBox()
        carbonates_6_1 = self.calculator.data_service.get_carbonate_formulas_table_6_1()
        carbonates_8_1 = (
            self.calculator.data_service.get_glass_carbonate_formulas_table_8_1()
        )
        all_carbonates = sorted(list(set(carbonates_6_1 + carbonates_8_1)))
        combo.addItems(all_carbonates)

        mass_input = QLineEdit()
        mass_input.setPlaceholderText("Масса, т")
        mass_validator = QDoubleValidator(0.0, 1e9, 6, self)
        mass_validator.setLocale(self.c_locale)
        mass_input.setValidator(mass_validator)
        mass_input.setToolTip("Годовое потребление данного вида карбонатного сырья.")

        calc_degree_input = QLineEdit("1.0")
        calc_degree_input.setPlaceholderText("Степень кальц., доля")
        calc_degree_validator = QDoubleValidator(0.0, 1.0, 4, self)
        calc_degree_validator.setLocale(self.c_locale)
        calc_degree_input.setValidator(calc_degree_validator)
        calc_degree_input.setToolTip(
            "Степень кальцинирования (доля от 0 до 1). По умолчанию 1.0 (100%)."
        )

        remove_button = QPushButton("Удалить")
        row_layout.addWidget(QLabel("Карбонат:"))
        row_layout.addWidget(combo)
        row_layout.addWidget(mass_input)
        row_layout.addWidget(calc_degree_input)
        row_layout.addWidget(remove_button)

        row_data = {
            "widget": row_widget,
            "combo": combo,
            "mass_input": mass_input,
            "calc_degree_input": calc_degree_input,
        }
        self.carbonate_rows.append(row_data)
        self.materials_layout.insertWidget(
            self.materials_layout.count() - 1, row_widget
        )
        remove_button.clicked.connect(lambda: self._remove_row(row_data))

    def _remove_row(self, row_data):
        row_widget = row_data["widget"]
        self.materials_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        self.carbonate_rows.remove(row_data)

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        try:
            if not self.carbonate_rows:
                raise ValueError("Добавьте хотя бы один вид карбонатного сырья.")

            carbonates_data = []
            for i, row in enumerate(self.carbonate_rows):
                name = row["combo"].currentText()
                mass = self._get_float(
                    row["mass_input"], f"Масса для '{name}' (строка {i+1})"
                )
                calc_degree = self._get_float(
                    row["calc_degree_input"],
                    f"Степень кальц. для '{name}' (строка {i+1})",
                )
                carbonates_data.append(
                    {"name": name, "mass": mass, "calcination_degree": calc_degree}
                )

            co2_emissions = self.calculator.calculate_emissions(carbonates_data)
            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")
            logging.info(f"Category 8 calculation successful: CO2={co2_emissions}")
        except ValueError as e:
            logging.error(f"Category 8 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 8 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Критическая ошибка", str(e))
            self.result_label.setText("Результат: Ошибка")
