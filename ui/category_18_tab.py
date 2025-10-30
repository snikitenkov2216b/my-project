# ui/category_18_tab.py - Виджет вкладки для расчетов по Категории 18.
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
    QRadioButton,
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_18 import Category18Calculator
from ui.tab_data_mixin import TabDataMixin



class Category18Tab(TabDataMixin, QWidget):
    """
    Класс виджета-вкладки для Категории 18 "Транспорт".
    """

    def __init__(self, calculator: Category18Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        transport_layout = QFormLayout()
        self.transport_type_combobox = QComboBox()
        self.transport_type_combobox.addItems(
            [
                "Автомобильный транспорт",
                "Железнодорожный транспорт",
                "Водный транспорт",
                "Воздушный транспорт",
            ]
        )
        transport_layout.addRow(
            "Выберите вид транспорта:", self.transport_type_combobox
        )
        main_layout.addLayout(transport_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_road_transport_widget())
        self.stacked_widget.addWidget(self._create_railway_transport_widget())
        self.stacked_widget.addWidget(self._create_water_transport_widget())
        self.stacked_widget.addWidget(self._create_air_transport_widget())
        main_layout.addWidget(self.stacked_widget)
        self.transport_type_combobox.currentIndexChanged.connect(
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

    def _create_line_edit(self, validator_params=None, tooltip=""):
        line_edit = QLineEdit()
        if validator_params:
            validator = QDoubleValidator(*validator_params, self)
            validator.setLocale(self.c_locale)
            line_edit.setValidator(validator)
        line_edit.setToolTip(tooltip)
        return line_edit

    def _create_road_transport_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.road_fuel_combobox = QComboBox()
        self.road_fuel_combobox.addItems(
            self.calculator.data_service.get_transport_fuel_names_18_1()
        )
        layout.addRow("Вид топлива:", self.road_fuel_combobox)
        self.road_consumption_input = self._create_line_edit(
            (0.0, 1e9, 6), "Введите общий расход топлива за год."
        )
        layout.addRow("Расход топлива:", self.road_consumption_input)
        self.road_unit_mass_radio = QRadioButton("Тонны")
        self.road_unit_volume_radio = QRadioButton("Литры")
        self.road_unit_mass_radio.setChecked(True)
        layout.addRow("Единицы измерения:", self.road_unit_mass_radio)
        layout.addRow("", self.road_unit_volume_radio)
        return widget

    def _create_railway_transport_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.rail_fuel_combobox = QComboBox()
        rail_fuels = [
            f
            for f in self.calculator.data_service.get_transport_fuel_names_18_1()
            if "дизельное" in f.lower()
        ]
        self.rail_fuel_combobox.addItems(rail_fuels)
        layout.addRow("Вид топлива:", self.rail_fuel_combobox)
        self.rail_consumption_input = self._create_line_edit(
            (0.0, 1e9, 6), "Расход дизельного топлива в тоннах."
        )
        layout.addRow("Расход топлива (тонн):", self.rail_consumption_input)
        return widget

    def _create_water_transport_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.water_fuel_combobox = QComboBox()
        water_fuels = [
            f
            for f in self.calculator.data_service.get_transport_fuel_names_18_1()
            if any(sub in f.lower() for sub in ["мазут", "дизельное", "флотский"])
        ]
        self.water_fuel_combobox.addItems(water_fuels)
        layout.addRow("Вид топлива:", self.water_fuel_combobox)
        self.water_consumption_input = self._create_line_edit(
            (0.0, 1e9, 6), "Расход топлива в тоннах."
        )
        layout.addRow("Расход топлива (тонн):", self.water_consumption_input)
        return widget

    def _create_air_transport_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.air_fuel_combobox = QComboBox()
        air_fuels = [
            f
            for f in self.calculator.data_service.get_transport_fuel_names_18_1()
            if any(sub in f.lower() for sub in ["авиационный", "топливо тс-1"])
        ]
        self.air_fuel_combobox.addItems(air_fuels)
        layout.addRow("Вид топлива:", self.air_fuel_combobox)
        self.air_consumption_input = self._create_line_edit(
            (0.0, 1e9, 6), "Расход авиационного топлива в тоннах."
        )
        layout.addRow("Расход топлива (тонн):", self.air_consumption_input)
        return widget

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        try:
            current_transport_index = self.transport_type_combobox.currentIndex()
            co2_emissions = 0.0

            if current_transport_index == 0:
                fuel_name = self.road_fuel_combobox.currentText()
                consumption = self._get_float(
                    self.road_consumption_input, "Расход топлива"
                )
                is_volume = self.road_unit_volume_radio.isChecked()
                co2_emissions = self.calculator.calculate_road_transport_emissions(
                    fuel_name, consumption, is_volume
                )
            elif current_transport_index == 1:
                fuel_name = self.rail_fuel_combobox.currentText()
                consumption = self._get_float(
                    self.rail_consumption_input, "Расход топлива"
                )
                co2_emissions = self.calculator.calculate_railway_transport_emissions(
                    fuel_name, consumption
                )
            elif current_transport_index == 2:
                fuel_name = self.water_fuel_combobox.currentText()
                consumption = self._get_float(
                    self.water_consumption_input, "Расход топлива"
                )
                co2_emissions = self.calculator.calculate_water_transport_emissions(
                    fuel_name, consumption
                )
            elif current_transport_index == 3:
                fuel_name = self.air_fuel_combobox.currentText()
                consumption = self._get_float(
                    self.air_consumption_input, "Расход топлива"
                )
                co2_emissions = self.calculator.calculate_air_transport_emissions(
                    fuel_name, consumption
                )

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")
            logging.info(f"Category 18 calculation successful: CO2={co2_emissions}")
        except ValueError as e:
            logging.error(f"Category 18 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 18 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Критическая ошибка", str(e))
            self.result_label.setText("Результат: Ошибка")
