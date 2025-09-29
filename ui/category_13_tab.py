# ui/category_13_tab.py - Виджет вкладки для расчетов по Категории 13.
# Реализует интерфейс для производства фторсодержащих веществ.
# Код написан полностью, без сокращений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_13 import Category13Calculator

class Category13Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 13 "Производство фторсодержащих веществ".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category13Calculator(self.data_service)
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # --- Выбор метода расчета ---
        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Расчет выбросов по коэффициентам (Ф. 13.2)",
            "Расчет выбросов по данным измерений (Ф. 13.1)",
            "Расчет коэффициента выбросов по данным измерений (Ф. 13.3)"
        ])
        method_layout.addRow("Выберите метод расчета:", self.method_combobox)
        main_layout.addLayout(method_layout)

        # --- Стек виджетов для разных методов ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_default_factors_widget())
        self.stacked_widget.addWidget(self._create_measurements_widget())
        self.stacked_widget.addWidget(self._create_ef_calculation_widget())
        main_layout.addWidget(self.stacked_widget)

        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_line_edit(self, validator_params):
        """Вспомогательная функция для создания поля ввода с валидатором."""
        line_edit = QLineEdit()
        validator = QDoubleValidator(*validator_params, self)
        validator.setLocale(self.c_locale)
        line_edit.setValidator(validator)
        return line_edit

    def _create_default_factors_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.process_combobox = QComboBox()
        self.process_combobox.addItems(["Производство ГХФУ-22 (выбросы CHF3)", "Производство SF6 (выбросы SF6)"])
        layout.addRow("Процесс и тип выброса:", self.process_combobox)

        self.production_mass_input = self._create_line_edit((0.0, 1e9, 6))
        layout.addRow("Масса произведенной основной продукции (т):", self.production_mass_input)
        
        self.emission_factor_input = self._create_line_edit((0.0, 1e9, 6))
        layout.addRow("Коэффициент выбросов (кг/т):", self.emission_factor_input)
        
        return widget

    def _create_measurements_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.gas_flow_input = self._create_line_edit((0.0, 1e12, 6))
        layout.addRow("Расход отходящих газов (м³/год):", self.gas_flow_input)
        
        self.concentration_input = self._create_line_edit((0.0, 1e9, 6))
        layout.addRow("Средняя концентрация парникового газа (мг/м³):", self.concentration_input)

        return widget

    def _create_ef_calculation_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.avg_gas_flow_input = self._create_line_edit((0.0, 1e9, 6))
        layout.addRow("Средний расход отходящих газов (м³/час):", self.avg_gas_flow_input)

        self.avg_concentration_input = self._create_line_edit((0.0, 1e9, 6))
        layout.addRow("Средняя концентрация парникового газа (мг/м³):", self.avg_concentration_input)
        
        self.avg_production_input = self._create_line_edit((0.0, 1e9, 6))
        layout.addRow("Среднее производство продукции (т/час):", self.avg_production_input)

        return widget

    def _get_float(self, line_edit, field_name):
        """Вспомогательная функция для получения числового значения из поля ввода."""
        text = line_edit.text().replace(',', '.')
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        current_method_index = self.method_combobox.currentIndex()
        try:
            if current_method_index == 0: # Расчет по коэффициентам
                production_mass = self._get_float(self.production_mass_input, "Масса продукции")
                emission_factor = self._get_float(self.emission_factor_input, "Коэффициент выбросов")
                
                emissions = self.calculator.calculate_emissions_with_default_factors(production_mass, emission_factor)
                gas_type = "CHF3" if "ГХФУ-22" in self.process_combobox.currentText() else "SF6"
                self.result_label.setText(f"Результат: {emissions:.4f} тонн {gas_type}")

            elif current_method_index == 1: # Расчет выбросов по измерениям
                gas_flow = self._get_float(self.gas_flow_input, "Расход отходящих газов")
                concentration = self._get_float(self.concentration_input, "Средняя концентрация")

                emissions = self.calculator.calculate_emissions_from_measurements(gas_flow, concentration)
                self.result_label.setText(f"Результат: {emissions:.4f} тонн парникового газа")

            elif current_method_index == 2: # Расчет EF по измерениям
                avg_gas_flow = self._get_float(self.avg_gas_flow_input, "Средний расход газов")
                avg_concentration = self._get_float(self.avg_concentration_input, "Средняя концентрация")
                avg_production = self._get_float(self.avg_production_input, "Среднее производство")

                emission_factor = self.calculator.calculate_ef_from_measurements(avg_gas_flow, avg_concentration, avg_production)
                self.result_label.setText(f"Результат: Коэффициент выбросов (EF) = {emission_factor:.4f} кг/т")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")