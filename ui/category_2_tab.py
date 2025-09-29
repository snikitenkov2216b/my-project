# ui/category_2_tab.py - Виджет вкладки для расчетов по Категории 2.
# Код обновлен для поддержки детализированных методов расчета по компонентному составу.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox,
    QLineEdit, QPushButton, QLabel, QMessageBox, QStackedWidget, QGroupBox, QHBoxLayout
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_2 import Category2Calculator

class Category2Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 2 "Сжигание в факелах".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category2Calculator(self.data_service)
        self.gas_composition_rows = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

        # --- Выбор метода расчета ---
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Расчет по стандартным коэффициентам (Формула 2.1)",
            "Расчет по компонентному составу (Формулы 2.2-2.5)"
        ])
        main_layout.addWidget(QLabel("Выберите метод расчета:"))
        main_layout.addWidget(self.method_combobox)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_default_factors_widget())
        self.stacked_widget.addWidget(self._create_composition_widget())
        main_layout.addWidget(self.stacked_widget)
        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)

        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_default_factors_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.gas_type_combobox = QComboBox()
        gas_types = self.data_service.get_flare_gas_types_table_2_1()
        self.gas_type_combobox.addItems(gas_types)
        layout.addRow("Вид сжигаемого газа:", self.gas_type_combobox)

        self.consumption_input = QLineEdit()
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        self.consumption_input.setValidator(validator)
        layout.addRow("Расход газа:", self.consumption_input)

        self.unit_combobox = QComboBox()
        self.unit_combobox.addItems(["тонна", "тыс. м3"])
        layout.addRow("Единицы измерения:", self.unit_combobox)
        
        return widget

    def _create_composition_widget(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Параметры для всего газа
        params_layout = QFormLayout()
        self.calc_basis_combobox = QComboBox()
        self.calc_basis_combobox.addItems(["По объему (Формула 2.2 и 2.4)", "По массе (Формула 2.3 и 2.5)"])
        params_layout.addRow("Основа расчета:", self.calc_basis_combobox)
        
        self.gas_density_input = QLineEdit()
        self.gas_density_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        params_layout.addRow("Плотность газовой смеси (кг/м³):", self.gas_density_input)

        self.inefficiency_factor_input = QLineEdit("0.02")
        self.inefficiency_factor_input.setValidator(QDoubleValidator(0.0, 1.0, 4, self))
        params_layout.addRow("Коэффициент недожога (CF):", self.inefficiency_factor_input)

        main_layout.addLayout(params_layout)

        # Динамические строки для компонентов
        group_box = QGroupBox("Компонентный состав газа")
        self.composition_layout = QVBoxLayout()
        group_box.setLayout(self.composition_layout)
        
        add_button = QPushButton("Добавить компонент")
        add_button.clicked.connect(self._add_composition_row)

        main_layout.addWidget(group_box)
        main_layout.addWidget(add_button)

        return widget

    def _add_composition_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        
        name_input = QLineEdit(placeholderText="Название (напр., CH4)")
        fraction_input = QLineEdit(placeholderText="Доля (%)")
        carbon_atoms_input = QLineEdit(placeholderText="Атомов C")
        molar_mass_input = QLineEdit(placeholderText="Молярная масса")
        
        for editor in [fraction_input, carbon_atoms_input, molar_mass_input]:
            validator = QDoubleValidator(0, 1e9, 6, self)
            validator.setLocale(self.c_locale)
            editor.setValidator(validator)
            
        remove_button = QPushButton("Удалить")
        
        row_layout.addWidget(name_input)
        row_layout.addWidget(fraction_input)
        row_layout.addWidget(carbon_atoms_input)
        row_layout.addWidget(molar_mass_input)
        row_layout.addWidget(remove_button)

        row_data = {'widget': row_widget, 'name': name_input, 'fraction': fraction_input, 
                    'carbon_atoms': carbon_atoms_input, 'molar_mass': molar_mass_input}
        self.gas_composition_rows.append(row_data)
        self.composition_layout.addWidget(row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data))

    def _remove_row(self, row_data):
        row_widget = row_data['widget']
        self.composition_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        self.gas_composition_rows.remove(row_data)

    def _perform_calculation(self):
        try:
            method_index = self.method_combobox.currentIndex()
            
            if method_index == 0: # Расчет по стандартным EF
                gas_type = self.gas_type_combobox.currentText()
                unit = self.unit_combobox.currentText()
                consumption_str = self.consumption_input.text().replace(',', '.')
                if not consumption_str: raise ValueError("Введите расход газа.")
                consumption = float(consumption_str)
                
                emissions = self.calculator.calculate_emissions_with_default_factors(
                    gas_type=gas_type, consumption=consumption, unit=unit
                )
                co2 = emissions.get('co2', 0.0)
                ch4 = emissions.get('ch4', 0.0)
                self.result_label.setText(f"Результат: {co2:.4f} т CO2, {ch4:.4f} т CH4")

            else: # Расчет по составу
                raise NotImplementedError("Расчет по компонентному составу будет реализован.")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except NotImplementedError:
             QMessageBox.information(self, "В разработке", "Этот метод расчета находится в разработке.")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")