# ui/category_11_tab.py - Виджет вкладки для расчетов по Категории 11.
# Реализует интерфейс для различных химических производств и методов расчета.
# Код написан полностью, без сокращений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_11 import Category11Calculator

class Category11Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 11 "Производство азотной кислоты,
    капролактама, глиоксаля и глиоксиловой кислоты".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category11Calculator(self.data_service)
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # --- Выбор метода расчета ---
        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Расчет выбросов по стандартным коэффициентам (Ф. 11.2)",
            "Расчет выбросов по данным измерений (Ф. 11.1)",
            "Расчет коэффициента выбросов по данным измерений (Ф. 11.3)"
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
        process_names = self.data_service.get_chemical_processes_table_11_1()
        self.process_combobox.addItems(process_names)
        layout.addRow("Производственный процесс:", self.process_combobox)
        
        self.production_mass_input = self._create_line_edit((0.0, 1e9, 6))
        self.production_mass_input.setToolTip("Годовой объем производства продукции, тонн.")
        layout.addRow("Масса произведенной продукции (т):", self.production_mass_input)
        
        return widget

    def _create_measurements_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.gas_flow_input = self._create_line_edit((0.0, 1e12, 6))
        self.gas_flow_input.setToolTip("Общий годовой расход отходящих газов с установки, м³/год.")
        layout.addRow("Расход отходящих газов (м³/год):", self.gas_flow_input)
        
        self.n2o_concentration_input = self._create_line_edit((0.0, 1e9, 6))
        self.n2o_concentration_input.setToolTip("Среднегодовая концентрация N2O в отходящих газах, мг/м³.")
        layout.addRow("Средняя концентрация N2O (мг/м³):", self.n2o_concentration_input)

        return widget

    def _create_ef_calculation_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.avg_gas_flow_input = self._create_line_edit((0.0, 1e9, 6))
        self.avg_gas_flow_input.setToolTip("Средний расход отходящих газов за период измерений, м³/час.")
        layout.addRow("Средний расход отходящих газов (м³/час):", self.avg_gas_flow_input)

        self.avg_n2o_concentration_input = self._create_line_edit((0.0, 1e9, 6))
        self.avg_n2o_concentration_input.setToolTip("Средняя концентрация N2O за период измерений, мг/м³.")
        layout.addRow("Средняя концентрация N2O (мг/м³):", self.avg_n2o_concentration_input)
        
        self.avg_production_input = self._create_line_edit((0.0, 1e9, 6))
        self.avg_production_input.setToolTip("Средний объем производства продукции за период измерений, т/час.")
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
            if current_method_index == 0: # Расчет по стандартным EF
                process_name = self.process_combobox.currentText()
                production_mass = self._get_float(self.production_mass_input, "Масса продукции")
                
                n2o_emissions = self.calculator.calculate_emissions_with_default_factors(process_name, production_mass)
                self.result_label.setText(f"Результат: {n2o_emissions:.4f} тонн N2O")

            elif current_method_index == 1: # Расчет выбросов по измерениям
                gas_flow = self._get_float(self.gas_flow_input, "Расход отходящих газов")
                concentration = self._get_float(self.n2o_concentration_input, "Средняя концентрация N2O")

                n2o_emissions = self.calculator.calculate_emissions_from_measurements(gas_flow, concentration)
                self.result_label.setText(f"Результат: {n2o_emissions:.4f} тонн N2O")

            elif current_method_index == 2: # Расчет EF по измерениям
                avg_gas_flow = self._get_float(self.avg_gas_flow_input, "Средний расход газов")
                avg_concentration = self._get_float(self.avg_n2o_concentration_input, "Средняя концентрация N2O")
                avg_production = self._get_float(self.avg_production_input, "Среднее производство")

                emission_factor = self.calculator.calculate_ef_from_measurements(avg_gas_flow, avg_concentration, avg_production)
                self.result_label.setText(f"Результат: Коэффициент выбросов (EF) = {emission_factor:.4f} кг N2O/т")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")