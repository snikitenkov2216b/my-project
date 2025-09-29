# ui/category_1_tab.py - Виджет вкладки для расчетов по Категории 1.
# Код обновлен для поддержки детализированных методов расчета.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QGroupBox, QHBoxLayout
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_1 import Category1Calculator

class Category1Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 1 "Стационарное сжигание топлива".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category1Calculator(self.data_service)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

        # --- Основные данные ---
        form_layout = QFormLayout()
        
        self.fuel_combobox = QComboBox()
        self.fuel_combobox.addItems(self.data_service.get_fuels_table_1_1())
        form_layout.addRow("Вид топлива:", self.fuel_combobox)

        self.fuel_consumption_input = QLineEdit()
        consumption_validator = QDoubleValidator(0.0, 1e9, 6, self)
        consumption_validator.setLocale(self.c_locale)
        self.fuel_consumption_input.setValidator(consumption_validator)
        form_layout.addRow("Расход топлива (в натуральных единицах):", self.fuel_consumption_input)
        
        main_layout.addLayout(form_layout)

        # --- Выбор метода расчета EF ---
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Использовать стандартный коэффициент выбросов (EF)",
            "Рассчитать EF на основе содержания углерода"
        ])
        main_layout.addWidget(QLabel("Метод определения коэффициента выбросов:"))
        main_layout.addWidget(self.method_combobox)
        
        self.ef_stacked_widget = QStackedWidget()
        # Пустой виджет для стандартного метода
        self.ef_stacked_widget.addWidget(QWidget()) 
        # Виджет для расчета EF по содержанию углерода
        self.ef_stacked_widget.addWidget(self._create_ef_from_carbon_widget())
        main_layout.addWidget(self.ef_stacked_widget)
        
        self.method_combobox.currentIndexChanged.connect(self.ef_stacked_widget.setCurrentIndex)
        
        # --- Коэффициент окисления ---
        oxidation_layout = QFormLayout()
        self.oxidation_factor_input = QLineEdit("1.0")
        oxidation_validator = QDoubleValidator(0.0, 1.0, 4, self)
        oxidation_validator.setLocale(self.c_locale)
        self.oxidation_factor_input.setValidator(oxidation_validator)
        oxidation_layout.addRow("Коэффициент окисления (доля):", self.oxidation_factor_input)
        main_layout.addLayout(oxidation_layout)
        
        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_ef_from_carbon_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.carbon_content_input = QLineEdit()
        validator = QDoubleValidator(0.0, 1.0, 6, self)
        validator.setLocale(self.c_locale)
        self.carbon_content_input.setValidator(validator)
        layout.addRow("Содержание углерода в топливе (доля, т C/т):", self.carbon_content_input)
        return widget
        
    def _perform_calculation(self):
        try:
            fuel_name = self.fuel_combobox.currentText()
            
            consumption_str = self.fuel_consumption_input.text().replace(',', '.')
            if not consumption_str:
                raise ValueError("Введите расход топлива.")
            fuel_consumption = float(consumption_str)

            oxidation_str = self.oxidation_factor_input.text().replace(',', '.')
            if not oxidation_str:
                raise ValueError("Введите коэффициент окисления.")
            oxidation_factor = float(oxidation_str)

            emission_factor = 0.0
            method_index = self.method_combobox.currentIndex()

            if method_index == 0: # Стандартный EF
                fuel_data = self.data_service.get_fuel_data_table_1_1(fuel_name)
                if not fuel_data or 'EF_CO2_ut' not in fuel_data:
                    raise ValueError(f"Стандартный коэффициент выбросов для '{fuel_name}' не найден.")
                emission_factor = fuel_data['EF_CO2_ut']
            
            elif method_index == 1: # Расчет по содержанию углерода
                carbon_str = self.carbon_content_input.text().replace(',', '.')
                if not carbon_str:
                    raise ValueError("Введите содержание углерода.")
                carbon_content = float(carbon_str)
                # Формула 1.5
                emission_factor = self.calculator.calculate_ef_from_carbon_content(carbon_content)

            # Формула 1.1
            co2_emissions = self.calculator.calculate_total_emissions(
                fuel_consumption=fuel_consumption,
                emission_factor=emission_factor,
                oxidation_factor=oxidation_factor
            )

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")