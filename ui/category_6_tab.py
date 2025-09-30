# ui/category_6_tab.py - Виджет вкладки для расчетов по Категории 6.
# Код обновлен для приема калькулятора из фабрики и для логирования.
# Комментарии на русском. Поддержка UTF-8.

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_6 import Category6Calculator

class Category6Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 6 "Производство цемента".
    """
    def __init__(self, calculator: Category6Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        
        self.raw_carbonate_rows = []
        self.raw_dust_carbonate_rows = []
        self.raw_non_carbonate_rows = []
        self.clinker_dust_oxide_rows = []
        self.clinker_non_carbonate_rows = []

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Расчет на основе расхода сырья (Формула 6.1)",
            "Расчет на основе производства клинкера (Формула 6.2)"
        ])
        method_layout.addRow("Выберите метод расчета:", self.method_combobox)
        main_layout.addLayout(method_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_raw_materials_widget())
        self.stacked_widget.addWidget(self._create_clinker_widget())
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

        dust_group = QGroupBox("Цементная пыль (CKD) (Формула 6.1)")
        dust_layout = QVBoxLayout(dust_group)
        dust_form = QFormLayout()
        self.raw_dust_mass_input = self._create_line_edit("0.0", (0.0, 1e9, 6))
        self.raw_dust_mass_input.setToolTip("Масса цементной пыли, уловленной и не возвращенной в печь.")
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

        non_carb_group = QGroupBox("Некарбонатное сырье с содержанием углерода")
        self.raw_non_carbonates_layout = QVBoxLayout(non_carb_group)
        add_non_carb_btn = QPushButton("Добавить некарбонатное сырье")
        add_non_carb_btn.clicked.connect(self._add_raw_non_carbonate_row)
        self.raw_non_carbonates_layout.addWidget(add_non_carb_btn)
        layout.addWidget(non_carb_group)

        scroll_area.setWidget(widget)
        return scroll_area

    def _create_clinker_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)

        clinker_group = QGroupBox("Производство клинкера и его состав")
        clinker_layout = QFormLayout(clinker_group)
        self.clinker_production_input = self._create_line_edit("", (0.0, 1e9, 6))
        self.clinker_production_input.setToolTip("Общая масса произведенного клинкера за год.")
        self.clinker_cao_fraction_input = self._create_line_edit("", (0.0, 1.0, 4), "Напр., 0.65")
        self.clinker_cao_fraction_input.setToolTip("Массовая доля оксида кальция (CaO) в клинкере.")
        self.clinker_mgo_fraction_input = self._create_line_edit("", (0.0, 1.0, 4), "Напр., 0.02")
        self.clinker_mgo_fraction_input.setToolTip("Массовая доля оксида магния (MgO) в клинкере.")
        clinker_layout.addRow("Масса клинкера (т):", self.clinker_production_input)
        clinker_layout.addRow("Массовая доля CaO в клинкере:", self.clinker_cao_fraction_input)
        clinker_layout.addRow("Массовая доля MgO в клинкере:", self.clinker_mgo_fraction_input)
        layout.addWidget(clinker_group)
        
        dust_group = QGroupBox("Цементная пыль (CKD) (Формула 6.2)")
        dust_layout = QVBoxLayout(dust_group)
        dust_form = QFormLayout()
        self.clinker_dust_mass_input = self._create_line_edit("0.0", (0.0, 1e9, 6))
        self.clinker_dust_mass_input.setToolTip("Масса цементной пыли, уловленной и не возвращенной в печь.")
        dust_form.addRow("Масса пыли (т):", self.clinker_dust_mass_input)
        dust_layout.addLayout(dust_form)
        self.clinker_dust_oxides_layout = QVBoxLayout()
        add_dust_oxide_btn = QPushButton("Добавить долю оксида в пыли")
        add_dust_oxide_btn.setToolTip("Добавьте оксидный состав пыли, если он известен.")
        add_dust_oxide_btn.clicked.connect(self._add_clinker_dust_oxide_row)
        dust_layout.addLayout(self.clinker_dust_oxides_layout)
        dust_layout.addWidget(add_dust_oxide_btn)
        layout.addWidget(dust_group)
        
        non_carb_group = QGroupBox("Некарбонатное сырье с содержанием углерода")
        self.clinker_non_carbonates_layout = QVBoxLayout(non_carb_group)
        add_non_carb_btn = QPushButton("Добавить некарбонатное сырье")
        add_non_carb_btn.clicked.connect(self._add_clinker_non_carbonate_row)
        self.clinker_non_carbonates_layout.addWidget(add_non_carb_btn)
        layout.addWidget(non_carb_group)
        
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
            self.calculator.data_service.get_carbonate_formulas_table_6_1(),
            [('mass', 'Масса, т', (0.0, 1e9, 6)), ('calc_degree', 'Степень кальц., доля', (0.0, 1.0, 4))])

    def _add_raw_dust_carbonate_row(self):
        self._create_dynamic_row(self.raw_dust_carbonate_rows, self.raw_dust_carbonates_layout,
            self.calculator.data_service.get_carbonate_formulas_table_6_1(),
            [('fraction', 'Доля в пыли', (0.0, 1.0, 4))])

    def _add_raw_non_carbonate_row(self):
        self._create_dynamic_row(self.raw_non_carbonate_rows, self.raw_non_carbonates_layout,
            self.calculator.data_service.get_fuels_table_1_1(),
            [('consumption', 'Расход, т', (0.0, 1e9, 6))])

    def _add_clinker_dust_oxide_row(self):
        self._create_dynamic_row(self.clinker_dust_oxide_rows, self.clinker_dust_oxides_layout,
            ['CaO', 'MgO'],
            [('fraction', 'Доля в пыли', (0.0, 1.0, 4))])

    def _add_clinker_non_carbonate_row(self):
        self._create_dynamic_row(self.clinker_non_carbonate_rows, self.clinker_non_carbonates_layout,
            self.calculator.data_service.get_fuels_table_1_1(),
            [('consumption', 'Расход, т', (0.0, 1e9, 6))])

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(',', '.')
        if not text: raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        try:
            current_method_index = self.method_combobox.currentIndex()
            co2_emissions = 0.0

            if current_method_index == 0:
                carbonates = [{'name': r['combo'].currentText(), 'mass': self._get_float(r['mass'], 'Масса карбоната'), 'calcination_degree': self._get_float(r['calc_degree'], 'Степень кальцинирования')} for r in self.raw_carbonate_rows]
                non_carbonates = [{'name': r['combo'].currentText(), 'consumption': self._get_float(r['consumption'], 'Расход некарбоната')} for r in self.raw_non_carbonate_rows]
                
                dust_mass = self._get_float(self.raw_dust_mass_input, 'Масса пыли')
                dust_calc_degree = self._get_float(self.raw_dust_calc_degree_input, 'Степень кальц. пыли')
                dust_fractions = [{'name': r['combo'].currentText(), 'fraction': self._get_float(r['fraction'], 'Доля карбоната в пыли')} for r in self.raw_dust_carbonate_rows]
                
                cement_dust = {'mass': dust_mass, 'calcination_degree': dust_calc_degree, 'carbonate_fractions': dust_fractions}
                if not carbonates: raise ValueError("Добавьте хотя бы один вид карбонатного сырья.")
                
                co2_emissions = self.calculator.calculate_based_on_raw_materials(carbonates, cement_dust, non_carbonates)

            elif current_method_index == 1:
                clinker_prod = self._get_float(self.clinker_production_input, 'Масса клинкера')
                cao_frac = self._get_float(self.clinker_cao_fraction_input, 'Доля CaO')
                mgo_frac = self._get_float(self.clinker_mgo_fraction_input, 'Доля MgO')
                clinker_comp = [{'oxide_name': 'CaO', 'fraction': cao_frac}, {'oxide_name': 'MgO', 'fraction': mgo_frac}]
                
                dust_mass = self._get_float(self.clinker_dust_mass_input, 'Масса пыли')
                dust_oxides = [{'oxide_name': r['combo'].currentText(), 'fraction': self._get_float(r['fraction'], 'Доля оксида в пыли')} for r in self.clinker_dust_oxide_rows]
                cement_dust = {'mass': dust_mass, 'oxide_composition': dust_oxides}

                non_carbonates = [{'name': r['combo'].currentText(), 'consumption': self._get_float(r['consumption'], 'Расход некарбоната')} for r in self.clinker_non_carbonate_rows]
                
                co2_emissions = self.calculator.calculate_based_on_clinker(clinker_prod, clinker_comp, cement_dust, non_carbonates)

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            logging.error(f"Category 6 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            logging.critical(f"Category 6 Calculation - Unexpected error: {e}", exc_info=True)
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")