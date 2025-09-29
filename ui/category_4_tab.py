# ui/category_4_tab.py - Виджет вкладки для расчетов по Категории 4.
# Реализует динамический интерфейс для различных процессов нефтепереработки.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_4 import Category4Calculator

class Category4Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 4 "Нефтепереработка".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category4Calculator(self.data_service)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Виджет выбора процесса ---
        process_layout = QFormLayout()
        self.process_combobox = QComboBox()
        self.process_combobox.addItems([
            "Регенерация катализаторов",
            "Прокалка нефтяного кокса",
            "Производство водорода"
        ])
        process_layout.addRow("Выберите процесс:", self.process_combobox)
        main_layout.addLayout(process_layout)
        
        # --- Стек виджетов для разных процессов ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_catalyst_regeneration_widget())
        self.stacked_widget.addWidget(self._create_coke_calcination_widget())
        self.stacked_widget.addWidget(self._create_hydrogen_production_widget())
        main_layout.addWidget(self.stacked_widget)

        self.process_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_catalyst_regeneration_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        
        self.coke_burnoff_input = QLineEdit()
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(c_locale)
        self.coke_burnoff_input.setValidator(validator)
        layout.addRow("Масса выгоревшего кокса (т):", self.coke_burnoff_input)

        self.coke_carbon_content_input = QLineEdit("0.94")
        validator = QDoubleValidator(0.0, 1.0, 4, self)
        validator.setLocale(c_locale)
        self.coke_carbon_content_input.setValidator(validator)
        layout.addRow("Содержание углерода в коксе (доля):", self.coke_carbon_content_input)
        
        return widget

    def _create_coke_calcination_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

        self.raw_coke_mass_input = QLineEdit()
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(c_locale)
        self.raw_coke_mass_input.setValidator(validator)
        layout.addRow("Количество сырого кокса (т):", self.raw_coke_mass_input)

        self.calcined_coke_mass_input = QLineEdit()
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(c_locale)
        self.calcined_coke_mass_input.setValidator(validator)
        layout.addRow("Количество прокаленного кокса (т):", self.calcined_coke_mass_input)

        self.dust_mass_input = QLineEdit()
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(c_locale)
        self.dust_mass_input.setValidator(validator)
        layout.addRow("Количество уловленной коксовой пыли (т):", self.dust_mass_input)
        
        return widget

    def _create_hydrogen_production_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

        self.feedstock_combobox = QComboBox()
        fuels = self.data_service.get_fuels_table_1_1()
        self.feedstock_combobox.addItems(fuels)
        self.feedstock_combobox.currentIndexChanged.connect(self._update_hydrogen_units)
        layout.addRow("Вид сырья (топлива):", self.feedstock_combobox)

        consumption_layout = QHBoxLayout()
        self.feedstock_consumption_input = QLineEdit()
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(c_locale)
        self.feedstock_consumption_input.setValidator(validator)

        self.hydrogen_units_label = QLabel()
        consumption_layout.addWidget(self.feedstock_consumption_input)
        consumption_layout.addWidget(self.hydrogen_units_label)
        layout.addRow("Расход сырья:", consumption_layout)
        
        self._update_hydrogen_units()
        return widget

    def _update_hydrogen_units(self):
        selected_fuel = self.feedstock_combobox.currentText()
        fuel_data = self.data_service.get_fuel_data_table_1_1(selected_fuel)
        if fuel_data and 'unit' in fuel_data:
            self.hydrogen_units_label.setText(f"({fuel_data['unit']})")
        else:
            self.hydrogen_units_label.setText("")

    def _perform_calculation(self):
        try:
            co2_emissions = 0.0
            current_process_index = self.process_combobox.currentIndex()

            if current_process_index == 0: # Регенерация катализаторов
                coke_burnoff_str = self.coke_burnoff_input.text().replace(',', '.')
                coke_carbon_content_str = self.coke_carbon_content_input.text().replace(',', '.')
                if not coke_burnoff_str or not coke_carbon_content_str: raise ValueError("Заполните все поля.")
                
                coke_burnoff = float(coke_burnoff_str)
                coke_carbon_content = float(coke_carbon_content_str)
                co2_emissions = self.calculator.calculate_catalyst_regeneration(coke_burnoff, coke_carbon_content)
            
            elif current_process_index == 1: # Прокалка кокса
                raw_coke_str = self.raw_coke_mass_input.text().replace(',', '.')
                calcined_coke_str = self.calcined_coke_mass_input.text().replace(',', '.')
                dust_str = self.dust_mass_input.text().replace(',', '.')
                if not all([raw_coke_str, calcined_coke_str, dust_str]): raise ValueError("Заполните все поля.")

                raw_coke = float(raw_coke_str)
                calcined_coke = float(calcined_coke_str)
                dust = float(dust_str)
                co2_emissions = self.calculator.calculate_coke_calcination(raw_coke, calcined_coke, dust)

            elif current_process_index == 2: # Производство водорода
                feedstock_name = self.feedstock_combobox.currentText()
                consumption_str = self.feedstock_consumption_input.text().replace(',', '.')
                if not consumption_str: raise ValueError("Заполните все поля.")
                
                consumption = float(consumption_str)
                co2_emissions = self.calculator.calculate_hydrogen_production(feedstock_name, consumption)

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", f"Пожалуйста, проверьте введенные данные. {e}")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")