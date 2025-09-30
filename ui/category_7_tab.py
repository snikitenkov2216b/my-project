# ui/category_7_tab.py - Виджет вкладки для расчетов по Категории 7.
# Реализует полный динамический интерфейс для производства извести,
# включая ввод данных по известковой пыли. Без упрощений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_7 import Category7Calculator

class Category7Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 7 "Производство извести".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category7Calculator(self.data_service)
        
        self.raw_carbonate_rows = []
        self.raw_dust_carbonate_rows = []
        self.lime_dust_oxide_rows = []

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Расчет на основе расхода сырья (Формула 7.1)",
            "Расчет на основе производства извести (Формула 7.2)"
        ])
        method_layout.addRow("Выберите метод расчета:", self.method_combobox)
        main_layout.addLayout(method_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_raw_materials_widget())
        self.stacked_widget.addWidget(self._create_lime_widget())
        main_layout.addWidget(self.stacked_widget)

        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)

        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_raw_materials_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)

        carb_group = QGroupBox("Основное карбонатное сырье")
        self.raw_carbonates_layout = QVBoxLayout(carb_group)
        add_carb_button = QPushButton("Добавить карбонат")
        add_carb_button.clicked.connect(self._add_raw_carbonate_row)
        self.raw_carbonates_layout.addWidget(add_carb_button)
        layout.addWidget(carb_group)

        dust_group = QGroupBox("Известковая пыль")
        dust_layout = QVBoxLayout(dust_group)
        dust_form = QFormLayout()
        self.raw_dust_mass_input = self._create_line_edit("0.0", (0.0, 1e9, 6))
        self.raw_dust_mass_input.setToolTip("Масса известковой пыли, уловленной и не возвращенной в печь.")
        self.raw_dust_calc_degree_input = self._create_line_edit("1.0", (0.0, 1.0, 4))
        self.raw_dust_calc_degree_input.setToolTip("Степень кальцинирования карбонатов в пыли (доля от 0 до 1).")
        dust_form.addRow("Масса пыли (т):", self.raw_dust_mass_input)
        dust_form.addRow("Степень кальцинирования пыли (доля):", self.raw_dust_calc_degree_input)
        dust_layout.addLayout(dust_form)
        
        self.raw_dust_carbonates_layout = QVBoxLayout()
        add_dust_carb_btn = QPushButton("Добавить долю карбоната в пыли")
        add_dust_carb_btn.setToolTip("Добавьте компонентный состав карбонатов в пыли, если он известен.")
        add_dust_carb_btn.clicked.connect(self._add_raw_dust_carbonate_row)
        dust_layout.addLayout(self.raw_dust_carbonates_layout)
        dust_layout.addWidget(add_dust_carb_btn)
        layout.addWidget(dust_group)
        
        scroll_area.setWidget(widget)
        return scroll_area

    def _create_lime_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)

        lime_group = QGroupBox("Производство извести и ее состав")
        lime_form = QFormLayout(lime_group)
        self.lime_production_input = self._create_line_edit("", (0.0, 1e9, 6))
        self.lime_production_input.setToolTip("Общая масса произведенной извести за отчетный период.")
        self.lime_cao_fraction_input = self._create_line_edit("", (0.0, 1.0, 4), "Напр., 0.95")
        self.lime_cao_fraction_input.setToolTip("Массовая доля оксида кальция (CaO) в извести.")
        self.lime_mgo_fraction_input = self._create_line_edit("", (0.0, 1.0, 4), "Напр., 0.01")
        self.lime_mgo_fraction_input.setToolTip("Массовая доля оксида магния (MgO) в извести.")
        lime_form.addRow("Масса произведенной извести (т):", self.lime_production_input)
        lime_form.addRow("Массовая доля CaO в извести:", self.lime_cao_fraction_input)
        lime_form.addRow("Массовая доля MgO в извести:", self.lime_mgo_fraction_input)
        layout.addWidget(lime_group)
        
        dust_group = QGroupBox("Известковая пыль")
        dust_layout = QVBoxLayout(dust_group)
        dust_form = QFormLayout()
        self.lime_dust_mass_input = self._create_line_edit("0.0", (0.0, 1e9, 6))
        self.lime_dust_mass_input.setToolTip("Масса известковой пыли, уловленной и не возвращенной в печь.")
        dust_form.addRow("Масса пыли (т):", self.lime_dust_mass_input)
        dust_layout.addLayout(dust_form)
        self.lime_dust_oxides_layout = QVBoxLayout()
        add_dust_oxide_btn = QPushButton("Добавить долю оксида в пыли")
        add_dust_oxide_btn.setToolTip("Добавьте оксидный состав пыли, если он известен.")
        add_dust_oxide_btn.clicked.connect(self._add_lime_dust_oxide_row)
        dust_layout.addLayout(self.lime_dust_oxides_layout)
        dust_layout.addWidget(add_dust_oxide_btn)
        layout.addWidget(dust_group)
        
        scroll_area.setWidget(widget)
        return scroll_area

    def _create_line_edit(self, default_text="", validator_params=None, placeholder=""):
        line_edit = QLineEdit(default_text)
        line_edit.setPlaceholderText(placeholder)
        if validator_params:
            validator = QDoubleValidator(*validator_params, self)
            validator.setLocale(self.c_locale)
            line_edit.setValidator(validator)
        return line_edit
    
    def _create_dynamic_row(self, storage, layout, items, fields):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_data = {'widget': row_widget}
        
        combo = QComboBox()
        combo.addItems(items)
        row_layout.addWidget(combo)
        row_data['combo'] = combo
        
        for field_key, placeholder, validator_params in fields:
            line_edit = self._create_line_edit("", validator_params, placeholder)
            row_layout.addWidget(line_edit)
            row_data[field_key] = line_edit
        
        remove_button = QPushButton("Удалить")
        row_layout.addWidget(remove_button)
        
        storage.append(row_data)
        layout.insertWidget(layout.count() - 1, row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data, layout, storage))

    def _remove_row(self, row_data, layout, storage):
        row_data['widget'].deleteLater()
        layout.removeWidget(row_data['widget'])
        storage.remove(row_data)

    def _add_raw_carbonate_row(self):
        self._create_dynamic_row(self.raw_carbonate_rows, self.raw_carbonates_layout, 
            self.data_service.get_carbonate_formulas_table_6_1(),
            [('mass', 'Масса, т', (0.0, 1e9, 6)), ('calc_degree', 'Степень кальц., доля', (0.0, 1.0, 4))])

    def _add_raw_dust_carbonate_row(self):
        self._create_dynamic_row(self.raw_dust_carbonate_rows, self.raw_dust_carbonates_layout,
            self.data_service.get_carbonate_formulas_table_6_1(),
            [('fraction', 'Доля в пыли', (0.0, 1.0, 4))])

    def _add_lime_dust_oxide_row(self):
        self._create_dynamic_row(self.lime_dust_oxide_rows, self.lime_dust_oxides_layout,
            ['CaO', 'MgO'],
            [('fraction', 'Доля в пыли', (0.0, 1.0, 4))])

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(',', '.')
        if not text: raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        try:
            current_method_index = self.method_combobox.currentIndex()
            co2_emissions = 0.0

            if current_method_index == 0: # Расчет по сырью
                carbonates = [{'name': r['combo'].currentText(), 'mass': self._get_float(r['mass'], 'Масса карбоната'), 'calcination_degree': self._get_float(r['calc_degree'], 'Степень кальцинирования')} for r in self.raw_carbonate_rows]
                
                dust_mass = self._get_float(self.raw_dust_mass_input, 'Масса пыли')
                dust_calc_degree = self._get_float(self.raw_dust_calc_degree_input, 'Степень кальц. пыли')
                dust_fractions = [{'name': r['combo'].currentText(), 'fraction': self._get_float(r['fraction'], 'Доля карбоната в пыли')} for r in self.raw_dust_carbonate_rows]
                lime_dust = {'mass': dust_mass, 'calcination_degree': dust_calc_degree, 'carbonate_fractions': dust_fractions}
                
                if not carbonates: raise ValueError("Добавьте хотя бы один вид карбонатного сырья.")
                co2_emissions = self.calculator.calculate_based_on_raw_materials(carbonates, lime_dust)

            elif current_method_index == 1: # Расчет по извести
                lime_prod = self._get_float(self.lime_production_input, 'Масса извести')
                cao_frac = self._get_float(self.lime_cao_fraction_input, 'Доля CaO')
                mgo_frac = self._get_float(self.lime_mgo_fraction_input, 'Доля MgO')
                lime_comp = [{'oxide_name': 'CaO', 'fraction': cao_frac}, {'oxide_name': 'MgO', 'fraction': mgo_frac}]
                
                dust_mass = self._get_float(self.lime_dust_mass_input, 'Масса пыли')
                dust_oxides = [{'oxide_name': r['combo'].currentText(), 'fraction': self._get_float(r['fraction'], 'Доля оксида в пыли')} for r in self.lime_dust_oxide_rows]
                lime_dust = {'mass': dust_mass, 'oxide_composition': dust_oxides}
                
                co2_emissions = self.calculator.calculate_based_on_lime(lime_prod, lime_comp, lime_dust)

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")