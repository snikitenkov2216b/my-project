# ui/category_11_tab.py - Виджет вкладки для расчетов по Категории 11.
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
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_11 import Category11Calculator
from ui.tab_data_mixin import TabDataMixin



class Category11Tab(TabDataMixin, QWidget):
    """
    Класс виджета-вкладки для Категории 11 "Производство азотной кислоты,
    капролактама, глиоксаля и глиоксиловой кислоты".
    """

    def __init__(self, calculator: Category11Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems(
            [
                "Расчет по стандартным коэффициентам (Ф. 11.2)",
                "Расчет по данным измерений (Ф. 11.1)",
                "Расчет коэффициента выбросов по данным измерений (Ф. 11.3)",
            ]
        )
        self.method_combobox.setToolTip(
            "Выберите наиболее подходящий метод в зависимости от наличия данных."
        )
        method_layout.addRow("Выберите метод расчета:", self.method_combobox)
        main_layout.addLayout(method_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_default_factors_widget())
        self.stacked_widget.addWidget(self._create_measurements_widget())
        self.stacked_widget.addWidget(self._create_ef_calculation_widget())
        main_layout.addWidget(self.stacked_widget)

        self.method_combobox.currentIndexChanged.connect(
            self.stacked_widget.setCurrentIndex
        )

        self.calculate_button = QPushButton("Рассчитать")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(
            self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_line_edit(self, validator_params=None, tooltip=""):
        line_edit = QLineEdit()
        if validator_params:
            validator = QDoubleValidator(*validator_params, self)
            validator.setLocale(self.c_locale)
            line_edit.setValidator(validator)
        line_edit.setToolTip(tooltip)
        return line_edit

    def _create_default_factors_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.process_combobox = QComboBox()
        process_names = self.calculator.data_service.get_chemical_processes_table_11_1()
        self.process_combobox.addItems(process_names)
        self.process_combobox.setToolTip("Выберите процесс из Таблицы 11.1 методики.")
        layout.addRow("Производственный процесс:", self.process_combobox)

        self.production_mass_input = self._create_line_edit(
            (0.0, 1e9, 6), "Годовой объем производства продукции, тонн."
        )
        layout.addRow("Масса продукции (т):", self.production_mass_input)

        return widget

    def _create_measurements_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.gas_flow_input = self._create_line_edit(
            (0.0, 1e12, 6), "Общий годовой расход отходящих газов с установки, м³/год."
        )
        layout.addRow("Расход отходящих газов (м³/год):", self.gas_flow_input)
        self.n2o_concentration_input = self._create_line_edit(
            (0.0, 1e9, 6), "Среднегодовая концентрация N2O в отходящих газах, мг/м³."
        )
        layout.addRow("Средняя концентрация N2O (мг/м³):", self.n2o_concentration_input)
        return widget

    def _create_ef_calculation_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.avg_gas_flow_input = self._create_line_edit(
            (0.0, 1e9, 6), "Средний расход отходящих газов за период измерений, м³/час."
        )
        layout.addRow("Средний расход газов (м³/час):", self.avg_gas_flow_input)
        self.avg_n2o_concentration_input = self._create_line_edit(
            (0.0, 1e9, 6), "Средняя концентрация N2O за период измерений, мг/м³."
        )
        layout.addRow(
            "Средняя концентрация N2O (мг/м³):", self.avg_n2o_concentration_input
        )
        self.avg_production_input = self._create_line_edit(
            (0.0, 1e9, 6),
            "Средний объем производства продукции за период измерений, т/час.",
        )
        layout.addRow("Среднее производство (т/час):", self.avg_production_input)
        return widget

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        current_method_index = self.method_combobox.currentIndex()
        try:
            if current_method_index == 0:
                process_name = self.process_combobox.currentText()
                production_mass = self._get_float(
                    self.production_mass_input, "Масса продукции"
                )
                n2o_emissions = (
                    self.calculator.calculate_emissions_with_default_factors(
                        process_name, production_mass
                    )
                )
                self.result_label.setText(f"Результат: {n2o_emissions:.4f} тонн N2O")
                logging.info(
                    f"Category 11 (default) calculation successful: N2O={n2o_emissions}"
                )
            elif current_method_index == 1:
                gas_flow = self._get_float(
                    self.gas_flow_input, "Расход отходящих газов"
                )
                concentration = self._get_float(
                    self.n2o_concentration_input, "Средняя концентрация N2O"
                )
                n2o_emissions = self.calculator.calculate_emissions_from_measurements(
                    gas_flow, concentration
                )
                self.result_label.setText(f"Результат: {n2o_emissions:.4f} тонн N2O")
                logging.info(
                    f"Category 11 (measurements) calculation successful: N2O={n2o_emissions}"
                )
            elif current_method_index == 2:
                avg_gas_flow = self._get_float(
                    self.avg_gas_flow_input, "Средний расход газов"
                )
                avg_concentration = self._get_float(
                    self.avg_n2o_concentration_input, "Средняя концентрация N2O"
                )
                avg_production = self._get_float(
                    self.avg_production_input, "Среднее производство"
                )
                emission_factor = self.calculator.calculate_ef_from_measurements(
                    avg_gas_flow, avg_concentration, avg_production
                )
                self.result_label.setText(
                    f"Результат: Коэффициент выбросов (EF) = {emission_factor:.4f} кг N2O/т"
                )
                logging.info(
                    f"Category 11 (EF calculation) successful: EF={emission_factor}"
                )
        except ValueError as e:
            logging.error(f"Category 11 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 11 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Критическая ошибка", str(e))
            self.result_label.setText("Результат: Ошибка")
