# ui/category_2_tab.py - Виджет вкладки для расчетов по Категории 2.
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
    QStackedWidget,
    QHBoxLayout,
    QGroupBox,
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_2 import Category2Calculator


class Category2Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 2 "Сжигание в факелах".
    """

    def __init__(self, calculator: Category2Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self.gas_composition_rows = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems(
            [
                "Расчет по стандартным коэффициентам (Формула 2.1)",
                "Расчет по компонентному составу (Формулы 2.2-2.5)",
            ]
        )
        self.method_combobox.setToolTip(
            "Выберите метод: по усредненным данным из справочника или по точному составу газа."
        )
        form_layout.addRow("Выберите метод расчета:", self.method_combobox)
        main_layout.addLayout(form_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_default_factors_widget())
        self.stacked_widget.addWidget(self._create_composition_widget())
        main_layout.addWidget(self.stacked_widget)
        self.method_combobox.currentIndexChanged.connect(
            self.stacked_widget.setCurrentIndex
        )

        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(
            self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_default_factors_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.gas_type_combobox = QComboBox()
        self.gas_type_combobox.addItems(
            self.calculator.data_service.get_flare_gas_types_table_2_1()
        )
        self.gas_type_combobox.setToolTip(
            "Выберите тип газа согласно Таблице 2.1 методики."
        )
        layout.addRow("Вид сжигаемого газа:", self.gas_type_combobox)

        self.consumption_input = QLineEdit()
        self.consumption_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        self.consumption_input.setToolTip(
            "Годовой объем или масса сжигаемого в факеле газа."
        )
        layout.addRow("Расход газа:", self.consumption_input)

        self.unit_combobox = QComboBox()
        self.unit_combobox.addItems(["тонна", "тыс. м3"])
        layout.addRow("Единицы измерения:", self.unit_combobox)

        return widget

    def _create_composition_widget(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        params_layout = QFormLayout()
        self.calc_basis_combobox = QComboBox()
        self.calc_basis_combobox.addItems(
            ["По объему (Формулы 2.2 и 2.4)", "По массе (Формулы 2.3 и 2.5)"]
        )
        params_layout.addRow("Основа расчета:", self.calc_basis_combobox)

        self.comp_gas_consumption_input = QLineEdit()
        self.comp_gas_consumption_input.setValidator(
            QDoubleValidator(0.0, 1e9, 6, self)
        )
        self.comp_gas_consumption_input.setToolTip(
            "Общий годовой объем сжигаемого газа в тыс. м³."
        )
        params_layout.addRow(
            "Общий расход газа (тыс. м³):", self.comp_gas_consumption_input
        )

        self.gas_density_input = QLineEdit()
        self.gas_density_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        self.gas_density_input.setToolTip(
            "Плотность газовой смеси, кг/м³. Требуется только для расчета по массе."
        )
        params_layout.addRow(
            "Плотность смеси (кг/м³, для расч. по массе):", self.gas_density_input
        )

        self.inefficiency_factor_input = QLineEdit("0.02")
        self.inefficiency_factor_input.setValidator(QDoubleValidator(0.0, 1.0, 4, self))
        self.inefficiency_factor_input.setToolTip(
            "Коэффициент недожога (CF). Значение по умолчанию 0.02 для нефтяных месторождений, 0.005 для предприятий."
        )
        params_layout.addRow(
            "Коэффициент недожога (CF, доля):", self.inefficiency_factor_input
        )
        main_layout.addLayout(params_layout)

        group_box = QGroupBox("Компонентный состав газа")
        self.composition_layout = QVBoxLayout(group_box)
        main_layout.addWidget(group_box)

        add_button = QPushButton("Добавить компонент")
        add_button.clicked.connect(self._add_composition_row)
        main_layout.addWidget(add_button)

        return widget

    def _add_composition_row(self):
        row = {"widget": QWidget()}
        layout = QHBoxLayout(row["widget"])
        row["name"] = QLineEdit(placeholderText="Название (напр., CH4)")
        row["fraction"] = QLineEdit(placeholderText="Доля, %")
        row["carbon_atoms"] = QLineEdit(placeholderText="Атомов C")
        row["molar_mass"] = QLineEdit(placeholderText="Молярная масса")
        remove_button = QPushButton("Удалить")
        layout.addWidget(row["name"])
        layout.addWidget(row["fraction"])
        layout.addWidget(row["carbon_atoms"])
        layout.addWidget(row["molar_mass"])
        layout.addWidget(remove_button)
        self.gas_composition_rows.append(row)
        self.composition_layout.addWidget(row["widget"])
        remove_button.clicked.connect(lambda: self._remove_row(row))

    def _remove_row(self, row_data):
        row_data["widget"].deleteLater()
        self.composition_layout.removeWidget(row_data["widget"])
        self.gas_composition_rows.remove(row_data)

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        try:
            method_index = self.method_combobox.currentIndex()
            result_text = "Результат: Ошибка"

            if method_index == 0:
                gas_type = self.gas_type_combobox.currentText()
                unit = self.unit_combobox.currentText()
                consumption = self._get_float(self.consumption_input, "Расход газа")
                emissions = self.calculator.calculate_emissions_with_default_factors(
                    gas_type, consumption, unit
                )
                co2, ch4 = emissions.get("co2", 0.0), emissions.get("ch4", 0.0)
                result_text = f"Результат: {co2:.4f} т CO2, {ch4:.4f} т CH4"
                logging.info(f"Category 2 (default) calculation: CO2={co2}, CH4={ch4}")

            elif method_index == 1:
                is_by_mass = self.calc_basis_combobox.currentIndex() == 1
                consumption = self._get_float(
                    self.comp_gas_consumption_input, "Общий расход газа"
                )
                inefficiency_factor = self._get_float(
                    self.inefficiency_factor_input, "Коэффициент недожога"
                )
                gas_density = (
                    self._get_float(self.gas_density_input, "Плотность")
                    if is_by_mass
                    else 0.0
                )
                if not self.gas_composition_rows:
                    raise ValueError("Добавьте хотя бы один компонент газа.")

                components = []
                ch4_fraction = 0.0
                total_fraction = 0
                for i, row in enumerate(self.gas_composition_rows):
                    name = row["name"].text()
                    fraction = self._get_float(row["fraction"], f"Доля {i+1}")
                    total_fraction += fraction
                    comp_data = {
                        "name": name,
                        "carbon_atoms": int(
                            self._get_float(row["carbon_atoms"], f"Атомы C {i+1}")
                        ),
                    }
                    if is_by_mass:
                        comp_data["mass_fraction"] = fraction
                        comp_data["molar_mass"] = self._get_float(
                            row["molar_mass"], f"Молярная масса {i+1}"
                        )
                    else:
                        comp_data["volume_fraction"] = fraction
                    if name.upper() == "CH4":
                        ch4_fraction = fraction
                    components.append(comp_data)

                if not (99.9 <= total_fraction <= 100.1):
                    raise ValueError(
                        f"Сумма долей компонентов ({total_fraction}%) должна быть равна 100%."
                    )

                ef_co2 = self.calculator.calculate_ef_co2(
                    components, inefficiency_factor, gas_density, is_by_mass
                )
                ef_ch4 = self.calculator.calculate_ef_ch4(
                    ch4_fraction, inefficiency_factor, is_by_mass
                )

                co2_emissions = consumption * ef_co2
                ch4_emissions = consumption * ef_ch4
                result_text = (
                    f"Результат: {co2_emissions:.4f} т CO2, {ch4_emissions:.4f} т CH4"
                )
                logging.info(
                    f"Category 2 (composition) calculation: CO2={co2_emissions}, CH4={ch4_emissions}"
                )

            self.result_label.setText(result_text)

        except ValueError as e:
            logging.error(f"Category 2 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 2 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(
                self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}"
            )
            self.result_label.setText("Результат: Ошибка")
