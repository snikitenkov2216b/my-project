# ui/category_4_tab.py - Виджет вкладки для расчетов по Категории 4.
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
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_4 import Category4Calculator
from ui.tab_data_mixin import TabDataMixin



class Category4Tab(TabDataMixin, QWidget):
    """
    Класс виджета-вкладки для Категории 4 "Нефтепереработка".
    """

    def __init__(self, calculator: Category4Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        process_layout = QFormLayout()
        self.process_combobox = QComboBox()
        self.process_combobox.addItems(
            [
                "Регенерация катализаторов (Формула 4.1)",
                "Прокалка нефтяного кокса (Формула 4.2)",
                "Производство водорода (Формула 4.3)",
            ]
        )
        self.process_combobox.setToolTip(
            "Выберите технологический процесс, для которого производится расчет."
        )
        process_layout.addRow("Выберите процесс:", self.process_combobox)
        main_layout.addLayout(process_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_catalyst_regeneration_widget())
        self.stacked_widget.addWidget(self._create_coke_calcination_widget())
        self.stacked_widget.addWidget(self._create_hydrogen_production_widget())
        main_layout.addWidget(self.stacked_widget)

        self.process_combobox.currentIndexChanged.connect(
            self.stacked_widget.setCurrentIndex
        )

        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(
            self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_line_edit(self, default_text="", validator_params=None, tooltip=""):
        line_edit = QLineEdit(default_text)
        if validator_params:
            validator = QDoubleValidator(*validator_params, self)
            validator.setLocale(self.c_locale)
            line_edit.setValidator(validator)
        if tooltip:
            line_edit.setToolTip(tooltip)
        return line_edit

    def _create_catalyst_regeneration_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.coke_burnoff_input = self._create_line_edit(
            validator_params=(0.0, 1e9, 6),
            tooltip="Общая масса кокса, выгоревшего с поверхности катализатора за год.",
        )
        layout.addRow("Масса выгоревшего кокса (т):", self.coke_burnoff_input)

        self.coke_carbon_content_input = self._create_line_edit(
            "0.94",
            (0.0, 1.0, 4),
            "Массовая доля углерода в коксе. Стандартное значение - 0.94.",
        )
        layout.addRow(
            "Содержание углерода в коксе (доля):", self.coke_carbon_content_input
        )
        return widget

    def _create_coke_calcination_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.raw_coke_mass_input = self._create_line_edit(
            validator_params=(0.0, 1e9, 6),
            tooltip="Масса сырого нефтяного кокса, поступившего на установку прокалки.",
        )
        layout.addRow("Количество сырого кокса (т):", self.raw_coke_mass_input)

        self.calcined_coke_mass_input = self._create_line_edit(
            validator_params=(0.0, 1e9, 6),
            tooltip="Масса прокаленного кокса, полученного на выходе с установки.",
        )
        layout.addRow(
            "Количество прокаленного кокса (т):", self.calcined_coke_mass_input
        )

        self.dust_mass_input = self._create_line_edit(
            "0.0", (0.0, 1e9, 6), "Масса коксовой пыли, уловленной системой очистки."
        )
        layout.addRow("Количество уловленной пыли (т):", self.dust_mass_input)
        return widget

    def _create_hydrogen_production_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.feedstock_combobox = QComboBox()
        self.feedstock_combobox.addItems(
            self.calculator.data_service.get_fuels_table_1_1()
        )
        self.feedstock_combobox.currentIndexChanged.connect(self._update_hydrogen_units)
        self.feedstock_combobox.setToolTip(
            "Выберите вид углеродсодержащего сырья, используемого для производства водорода."
        )
        layout.addRow("Вид сырья (топлива):", self.feedstock_combobox)

        consumption_layout = QHBoxLayout()
        self.feedstock_consumption_input = self._create_line_edit(
            validator_params=(0.0, 1e9, 6),
            tooltip="Годовой расход сырья для производства водорода.",
        )
        self.hydrogen_units_label = QLabel()
        consumption_layout.addWidget(self.feedstock_consumption_input)
        consumption_layout.addWidget(self.hydrogen_units_label)
        layout.addRow("Расход сырья:", consumption_layout)

        self._update_hydrogen_units()
        return widget

    def _update_hydrogen_units(self):
        selected_fuel = self.feedstock_combobox.currentText()
        fuel_data = self.calculator.data_service.get_fuel_data_table_1_1(selected_fuel)
        unit = fuel_data.get("unit", "") if fuel_data else ""
        self.hydrogen_units_label.setText(f"({unit})")

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        try:
            co2_emissions = 0.0
            current_process_index = self.process_combobox.currentIndex()

            if current_process_index == 0:
                coke_burnoff = self._get_float(
                    self.coke_burnoff_input, "Масса выгоревшего кокса"
                )
                coke_carbon_content = self._get_float(
                    self.coke_carbon_content_input, "Содержание углерода в коксе"
                )
                co2_emissions = self.calculator.calculate_catalyst_regeneration(
                    coke_burnoff, coke_carbon_content
                )

            elif current_process_index == 1:
                raw_coke = self._get_float(
                    self.raw_coke_mass_input, "Количество сырого кокса"
                )
                calcined_coke = self._get_float(
                    self.calcined_coke_mass_input, "Количество прокаленного кокса"
                )
                dust = self._get_float(
                    self.dust_mass_input, "Количество уловленной пыли"
                )
                co2_emissions = self.calculator.calculate_coke_calcination(
                    raw_coke, calcined_coke, dust
                )

            elif current_process_index == 2:
                feedstock_name = self.feedstock_combobox.currentText()
                consumption = self._get_float(
                    self.feedstock_consumption_input, "Расход сырья"
                )
                co2_emissions = self.calculator.calculate_hydrogen_production(
                    feedstock_name, consumption
                )

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")
            logging.info(
                f"Category 4 calculation successful: Process={current_process_index}, CO2={co2_emissions}"
            )

        except ValueError as e:
            logging.error(f"Category 4 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 4 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(
                self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}"
            )
            self.result_label.setText("Результат: Ошибка")
