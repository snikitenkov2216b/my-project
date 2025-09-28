# ui/category_18_tab.py - Виджет вкладки для расчетов по Категории 18.
# Реализует интерфейс для различных видов транспорта.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QRadioButton
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale # <--- ДОБАВЛЕН ИМПОРТ QLocale

from data_models import DataService
from calculations.category_18 import Category18Calculator

class Category18Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 18 "Транспорт".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category18Calculator(self.data_service)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Создаем локаль один раз для всего класса
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

        self.transport_type_combobox = QComboBox()
        self.transport_type_combobox.addItems(["Автомобильный", "Железнодорожный", "Водный", "Воздушный"])
        main_layout.addWidget(QLabel("Выберите вид транспорта:"))
        main_layout.addWidget(self.transport_type_combobox)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_road_transport_widget())
        self.stacked_widget.addWidget(self._create_railway_transport_widget())
        self.stacked_widget.addWidget(self._create_water_transport_widget())
        self.stacked_widget.addWidget(self._create_air_transport_widget())
        main_layout.addWidget(self.stacked_widget)

        self.transport_type_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)

        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_road_transport_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.road_fuel_combobox = QComboBox()
        road_fuels = [f['fuel'] for f in self.data_service.table_18_1 if f['rho'] is not None and 'СНГ' not in f['fuel']]
        self.road_fuel_combobox.addItems(road_fuels)
        layout.addRow("Вид топлива:", self.road_fuel_combobox)

        self.road_consumption_input = QLineEdit()
        road_validator = QDoubleValidator(0.0, 1e9, 6, self)
        road_validator.setLocale(self.c_locale)
        self.road_consumption_input.setValidator(road_validator)
        layout.addRow("Расход топлива:", self.road_consumption_input)
        
        self.road_unit_mass_radio = QRadioButton("тонны")
        self.road_unit_volume_radio = QRadioButton("литры")
        self.road_unit_mass_radio.setChecked(True)
        layout.addRow(self.road_unit_mass_radio, self.road_unit_volume_radio)

        return widget

    def _create_railway_transport_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.rail_fuel_combobox = QComboBox()
        rail_fuels = [f['fuel'] for f in self.data_service.table_18_1 if f['fuel'] in ['Дизельное топливо летнее', 'Дизельное топливо зимнее', 'Дизельное топливо арктическое', 'Сжиженный природный газ (СПГ)', 'Топочный мазут'] or 'уголь' in f['fuel'].lower()]
        self.rail_fuel_combobox.addItems(rail_fuels)
        layout.addRow("Вид топлива:", self.rail_fuel_combobox)
        
        self.rail_consumption_input = QLineEdit()
        rail_validator = QDoubleValidator(0.0, 1e9, 6, self)
        rail_validator.setLocale(self.c_locale)
        self.rail_consumption_input.setValidator(rail_validator)
        layout.addRow("Расход топлива (тонн):", self.rail_consumption_input)

        return widget

    def _create_water_transport_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.water_fuel_combobox = QComboBox()
        water_fuels = [f['fuel'] for f in self.data_service.table_18_1 if f['fuel'] in ['Мазут флотский', 'Дизельное топливо летнее', 'Дизельное топливо зимнее', 'Дизельное топливо арктическое', 'Газ сжиженный']]
        self.water_fuel_combobox.addItems(water_fuels)
        layout.addRow("Вид топлива:", self.water_fuel_combobox)
        
        self.water_consumption_input = QLineEdit()
        water_validator = QDoubleValidator(0.0, 1e9, 6, self)
        water_validator.setLocale(self.c_locale)
        self.water_consumption_input.setValidator(water_validator)
        layout.addRow("Расход топлива (тонн):", self.water_consumption_input)
        
        return widget
        
    def _create_air_transport_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.air_fuel_combobox = QComboBox()
        air_fuels = [f['fuel'] for f in self.data_service.table_18_1 if 'авиационный' in f['fuel'].lower() or 'реактивных' in f['fuel'].lower()]
        self.air_fuel_combobox.addItems(air_fuels)
        layout.addRow("Вид топлива:", self.air_fuel_combobox)
        
        self.air_consumption_input = QLineEdit()
        air_validator = QDoubleValidator(0.0, 1e9, 6, self)
        air_validator.setLocale(self.c_locale)
        self.air_consumption_input.setValidator(air_validator)
        layout.addRow("Расход топлива (тонн):", self.air_consumption_input)
        
        return widget

    def _perform_calculation(self):
        try:
            current_index = self.transport_type_combobox.currentIndex()
            co2_emissions = 0.0

            if current_index == 0: # Автомобильный
                fuel = self.road_fuel_combobox.currentText()
                consumption_str = self.road_consumption_input.text().replace(',', '.')
                if not consumption_str: raise ValueError("Введите расход топлива.")
                consumption = float(consumption_str)
                is_volume = self.road_unit_volume_radio.isChecked()
                co2_emissions = self.calculator.calculate_road_transport_emissions(fuel, consumption, is_volume)
            
            elif current_index == 1: # Железнодорожный
                fuel = self.rail_fuel_combobox.currentText()
                consumption_str = self.rail_consumption_input.text().replace(',', '.')
                if not consumption_str: raise ValueError("Введите расход топлива.")
                consumption = float(consumption_str)
                co2_emissions = self.calculator.calculate_railway_transport_emissions(fuel, consumption)

            elif current_index == 2: # Водный
                fuel = self.water_fuel_combobox.currentText()
                consumption_str = self.water_consumption_input.text().replace(',', '.')
                if not consumption_str: raise ValueError("Введите расход топлива.")
                consumption = float(consumption_str)
                co2_emissions = self.calculator.calculate_water_transport_emissions(fuel, consumption)

            elif current_index == 3: # Воздушный
                fuel = self.air_fuel_combobox.currentText()
                consumption_str = self.air_consumption_input.text().replace(',', '.')
                if not consumption_str: raise ValueError("Введите расход топлива.")
                consumption = float(consumption_str)
                co2_emissions = self.calculator.calculate_air_transport_emissions(fuel, consumption)

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")