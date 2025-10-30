# ui/category_9_tab.py - Виджет вкладки для расчетов по Категории 9.
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
    QGroupBox,
    QScrollArea,
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_9 import Category9Calculator
from ui.tab_data_mixin import TabDataMixin



class Category9Tab(TabDataMixin, QWidget):
    """
    Класс виджета-вкладки для Категории 9 "Производство керамических изделий".
    """

    def __init__(self, calculator: Category9Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.raw_material_rows = []
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

        group_box = QGroupBox("Минеральное сырье, содержащее карбонаты")
        self.materials_layout = QVBoxLayout(group_box)

        add_button = QPushButton("Добавить сырье")
        add_button.clicked.connect(self._add_material_row)
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

    def _add_material_row(self):
        """Добавляет новую динамическую строку для ввода данных по сырью."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)

        carbonate_combo = QComboBox()
        carbonate_names = (
            self.calculator.data_service.get_carbonate_formulas_table_6_1()
        )
        carbonate_combo.addItems(carbonate_names)

        mass_input = QLineEdit()
        mass_input.setPlaceholderText("Масса сырья, т")
        mass_validator = QDoubleValidator(0.0, 1e9, 6, self)
        mass_validator.setLocale(self.c_locale)
        mass_input.setValidator(mass_validator)
        mass_input.setToolTip(
            "Общая масса минерального сырья (например, глины), содержащего данный карбонат."
        )

        fraction_input = QLineEdit()
        fraction_input.setPlaceholderText("Доля карбоната (0-1)")
        fraction_validator = QDoubleValidator(0.0, 1.0, 4, self)
        fraction_validator.setLocale(self.c_locale)
        fraction_input.setValidator(fraction_validator)
        fraction_input.setToolTip(
            "Массовая доля выбранного карбоната в данном виде сырья (например, 0.1 для 10%)."
        )

        calc_degree_input = QLineEdit("1.0")
        calc_degree_input.setPlaceholderText("Степень кальц., доля")
        calc_degree_validator = QDoubleValidator(0.0, 1.0, 4, self)
        calc_degree_validator.setLocale(self.c_locale)
        calc_degree_input.setValidator(calc_degree_validator)
        calc_degree_input.setToolTip(
            "Степень кальцинирования (доля от 0 до 1). По умолчанию 1.0 (100%), что означает полное разложение карбоната."
        )

        remove_button = QPushButton("Удалить")

        row_layout.addWidget(QLabel("Карбонат в сырье:"))
        row_layout.addWidget(carbonate_combo)
        row_layout.addWidget(mass_input)
        row_layout.addWidget(fraction_input)
        row_layout.addWidget(calc_degree_input)
        row_layout.addWidget(remove_button)

        row_data = {
            "widget": row_widget,
            "carbonate_combo": carbonate_combo,
            "mass_input": mass_input,
            "fraction_input": fraction_input,
            "calc_degree_input": calc_degree_input,
        }
        self.raw_material_rows.append(row_data)
        self.materials_layout.insertWidget(
            self.materials_layout.count() - 1, row_widget
        )

        remove_button.clicked.connect(lambda: self._remove_row(row_data))

    def _remove_row(self, row_data):
        """Удаляет строку из интерфейса и из списка хранения."""
        row_widget = row_data["widget"]
        self.materials_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        self.raw_material_rows.remove(row_data)

    def _get_float(self, line_edit, field_name):
        """Вспомогательная функция для получения числового значения из поля ввода."""
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        """Выполняет расчет на основе введенных данных."""
        try:
            if not self.raw_material_rows:
                raise ValueError("Добавьте хотя бы один вид минерального сырья.")

            materials_data = []
            for i, row in enumerate(self.raw_material_rows):
                carbonate_name = row["carbonate_combo"].currentText()
                mass = self._get_float(row["mass_input"], f"Масса сырья (строка {i+1})")
                fraction = self._get_float(
                    row["fraction_input"], f"Доля карбоната (строка {i+1})"
                )
                calc_degree = self._get_float(
                    row["calc_degree_input"], f"Степень кальцинирования (строка {i+1})"
                )

                materials_data.append(
                    {
                        "carbonate_name": carbonate_name,
                        "material_mass": mass,
                        "carbonate_fraction": fraction,
                        "calcination_degree": calc_degree,
                    }
                )

            co2_emissions = self.calculator.calculate_emissions(materials_data)

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")
            logging.info(f"Category 9 calculation successful: CO2={co2_emissions}")

        except ValueError as e:
            logging.error(f"Category 9 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 9 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(
                self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}"
            )
            self.result_label.setText("Результат: Ошибка")
