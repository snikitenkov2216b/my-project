# ui/category_1_tab.py - Виджет вкладки для расчетов по Категории 1.
# Код полностью реализует интерфейс для всех методов расчета, включая
# динамическое добавление компонентов газа. Без заглушек.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox
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
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        
        self.gas_volume_rows = []
        self.gas_mass_rows = []
        
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout = QFormLayout()
        self.fuel_combobox = QComboBox()
        self.fuel_combobox.addItems(self.data_service.get_fuels_table_1_1())
        form_layout.addRow("Вид топлива:", self.fuel_combobox)

        self.fuel_consumption_input = QLineEdit()
        # ИСПРАВЛЕНО: Раздельная инициализация валидатора и установка локали
        validator_consumption = QDoubleValidator(0.0, 1e12, 6, self)
        validator_consumption.setLocale(self.c_locale)
        self.fuel_consumption_input.setValidator(validator_consumption)
        form_layout.addRow("Расход топлива (в натуральных единицах):", self.fuel_consumption_input)
        main_layout.addLayout(form_layout)

        ef_group = QGroupBox("Расчет коэффициента выбросов (EF)")
        ef_layout = QVBoxLayout(ef_group)
        
        self.ef_method_combobox = QComboBox()
        self.ef_method_combobox.addItems([
            "Использовать стандартный EF (из Таблицы 1.1)",
            "Расчет EF по содержанию углерода (Формула 1.5)",
            "Расчет EF по объемному составу газа (Формула 1.3)",
            "Расчет EF по массовому составу газа (Формула 1.4)"
        ])
        ef_layout.addWidget(QLabel("Метод определения EF:"))
        ef_layout.addWidget(self.ef_method_combobox)
        
        self.ef_stacked_widget = QStackedWidget()
        self.ef_stacked_widget.addWidget(QWidget())
        self.ef_stacked_widget.addWidget(self._create_ef_from_carbon_widget())
        self.ef_stacked_widget.addWidget(self._create_ef_from_gas_volume_widget())
        self.ef_stacked_widget.addWidget(self._create_ef_from_gas_mass_widget())
        ef_layout.addWidget(self.ef_stacked_widget)
        self.ef_method_combobox.currentIndexChanged.connect(self.ef_stacked_widget.setCurrentIndex)
        main_layout.addWidget(ef_group)

        self.oxidation_factor_input = QLineEdit("1.0")
        # ИСПРАВЛЕНО: Раздельная инициализация валидатора и установка локали
        validator_oxidation = QDoubleValidator(0.0, 1.0, 4, self)
        validator_oxidation.setLocale(self.c_locale)
        self.oxidation_factor_input.setValidator(validator_oxidation)
        ox_layout = QFormLayout()
        ox_layout.addRow("Коэффициент окисления (OF):", self.oxidation_factor_input)
        main_layout.addLayout(ox_layout)
        
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
        # ИСПРАВЛЕНО
        validator = QDoubleValidator(0.0, 1.0, 6, self)
        validator.setLocale(self.c_locale)
        self.carbon_content_input.setValidator(validator)
        layout.addRow("Содержание углерода в топливе (доля, т C/т):", self.carbon_content_input)
        return widget
        
    def _create_ef_from_gas_volume_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()
        self.rho_co2_input = QLineEdit(str(self.data_service.get_density_data_table_1_2()['rho_CO2']))
        # ИСПРАВЛЕНО
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        self.rho_co2_input.setValidator(validator)
        form.addRow("Плотность CO₂, кг/м³:", self.rho_co2_input)
        layout.addLayout(form)

        group_box = QGroupBox("Компоненты газа (объемные доли)")
        self.gas_volume_layout = QVBoxLayout(group_box)
        layout.addWidget(group_box)
        add_button = QPushButton("Добавить компонент")
        add_button.clicked.connect(self._add_gas_volume_row)
        layout.addWidget(add_button)
        return widget

    def _create_ef_from_gas_mass_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()
        self.fuel_density_input = QLineEdit()
        # ИСПРАВЛЕНО
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        self.fuel_density_input.setValidator(validator)
        form.addRow("Плотность топлива, кг/м³:", self.fuel_density_input)
        layout.addLayout(form)
        
        group_box = QGroupBox("Компоненты газа (массовые доли)")
        self.gas_mass_layout = QVBoxLayout(group_box)
        layout.addWidget(group_box)
        add_button = QPushButton("Добавить компонент")
        add_button.clicked.connect(self._add_gas_mass_row)
        layout.addWidget(add_button)
        return widget

    def _add_gas_volume_row(self):
        row = {'widget': QWidget()}
        layout = QHBoxLayout(row['widget'])
        row['fraction'] = QLineEdit(placeholderText="Доля, %")
        row['carbon_atoms'] = QLineEdit(placeholderText="Атомов C")
        remove_button = QPushButton("Удалить")
        layout.addWidget(row['fraction'])
        layout.addWidget(row['carbon_atoms'])
        layout.addWidget(remove_button)
        self.gas_volume_rows.append(row)
        self.gas_volume_layout.addWidget(row['widget'])
        remove_button.clicked.connect(lambda: self._remove_row(row, self.gas_volume_layout, self.gas_volume_rows))

    def _add_gas_mass_row(self):
        row = {'widget': QWidget()}
        layout = QHBoxLayout(row['widget'])
        row['fraction'] = QLineEdit(placeholderText="Доля, %")
        row['carbon_atoms'] = QLineEdit(placeholderText="Атомов C")
        row['molar_mass'] = QLineEdit(placeholderText="Молярная масса")
        remove_button = QPushButton("Удалить")
        layout.addWidget(row['fraction'])
        layout.addWidget(row['carbon_atoms'])
        layout.addWidget(row['molar_mass'])
        layout.addWidget(remove_button)
        self.gas_mass_rows.append(row)
        self.gas_mass_layout.addWidget(row['widget'])
        remove_button.clicked.connect(lambda: self._remove_row(row, self.gas_mass_layout, self.gas_mass_rows))

    def _remove_row(self, row, layout, storage):
        row['widget'].deleteLater()
        layout.removeWidget(row['widget'])
        storage.remove(row)

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(',', '.')
        if not text: raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        try:
            fuel_name = self.fuel_combobox.currentText()
            fuel_consumption = self._get_float(self.fuel_consumption_input, "Расход топлива")
            oxidation_factor = self._get_float(self.oxidation_factor_input, "Коэффициент окисления")
            
            emission_factor = 0.0
            method_index = self.ef_method_combobox.currentIndex()

            if method_index == 0: # Стандартный EF
                fuel_data = self.data_service.get_fuel_data_table_1_1(fuel_name)
                if not fuel_data or 'EF_CO2_ut' not in fuel_data:
                    raise ValueError(f"Стандартный EF для '{fuel_name}' не найден.")
                emission_factor = fuel_data['EF_CO2_ut']
            
            elif method_index == 1: # Расчет по содержанию углерода
                carbon_content = self._get_float(self.carbon_content_input, "Содержание углерода")
                emission_factor = self.calculator.calculate_ef_from_carbon_content(carbon_content)
            
            elif method_index == 2: # Расчет по объемному составу
                rho_co2 = self._get_float(self.rho_co2_input, "Плотность CO2")
                components = []
                for i, row in enumerate(self.gas_volume_rows):
                    fraction = self._get_float(row['fraction'], f"Доля компонента {i+1}")
                    atoms = int(self._get_float(row['carbon_atoms'], f"Атомы C компонента {i+1}"))
                    components.append({'volume_fraction': fraction, 'carbon_atoms': atoms})
                if not components: raise ValueError("Добавьте хотя бы один компонент газа.")
                emission_factor = self.calculator.calculate_ef_from_gas_composition_volume(components, rho_co2)

            elif method_index == 3: # Расчет по массовому составу
                fuel_density = self._get_float(self.fuel_density_input, "Плотность топлива")
                components = []
                for i, row in enumerate(self.gas_mass_rows):
                    fraction = self._get_float(row['fraction'], f"Доля компонента {i+1}")
                    atoms = int(self._get_float(row['carbon_atoms'], f"Атомы C компонента {i+1}"))
                    molar_mass = self._get_float(row['molar_mass'], f"Молярная масса компонента {i+1}")
                    components.append({'mass_fraction': fraction, 'carbon_atoms': atoms, 'molar_mass': molar_mass})
                if not components: raise ValueError("Добавьте хотя бы один компонент газа.")
                emission_factor = self.calculator.calculate_ef_from_gas_composition_mass(components, fuel_density)

            co2_emissions = self.calculator.calculate_total_emissions(
                fuel_consumption, emission_factor, oxidation_factor
            )

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")