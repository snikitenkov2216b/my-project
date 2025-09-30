# ui/category_12_tab.py - Виджет вкладки для расчетов по Категории 12.
# Код обновлен для приема калькулятора из фабрики и для логирования.
# Комментарии на русском. Поддержка UTF-8.

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_12 import Category12Calculator

class Category12Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 12 "Нефтехимическое производство".
    """
    def __init__(self, calculator: Category12Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        
        self.balance_raw_materials = []
        self.balance_primary_products = []
        self.balance_by_products = []
        self.source_stationary_fuels = []
        self.source_flare_gases = []
        self.source_fugitive_gases = []

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Метод углеродного баланса (Формула 12.1)",
            "Метод по категориям источников (Формула 12.2)"
        ])
        method_layout.addRow("Выберите метод расчета:", self.method_combobox)
        main_layout.addLayout(method_layout)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_balance_widget())
        self.stacked_widget.addWidget(self._create_source_categories_widget())
        main_layout.addWidget(self.stacked_widget)
        
        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_scrollable_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(widget)
        return scroll_area, layout

    def _create_balance_widget(self):
        scroll_area, layout = self._create_scrollable_widget()
        
        raw_group = QGroupBox("Сырье (входящий поток)")
        self.balance_raw_layout = QVBoxLayout(raw_group)
        add_raw_btn = QPushButton("Добавить сырье")
        add_raw_btn.clicked.connect(self._add_balance_raw_row)
        self.balance_raw_layout.addWidget(add_raw_btn)
        layout.addWidget(raw_group)

        prod_group = QGroupBox("Продукция (выходящий поток)")
        prod_layout = QVBoxLayout(prod_group)
        prod_layout.addWidget(QLabel("Основная продукция:"))
        self.balance_primary_layout = QVBoxLayout()
        add_primary_btn = QPushButton("Добавить основную продукцию")
        add_primary_btn.clicked.connect(self._add_balance_primary_row)
        prod_layout.addLayout(self.balance_primary_layout)
        prod_layout.addWidget(add_primary_btn)
        
        prod_layout.addWidget(QLabel("Сопутствующая продукция:"))
        self.balance_by_prod_layout = QVBoxLayout()
        add_by_prod_btn = QPushButton("Добавить сопутствующую продукцию")
        add_by_prod_btn.clicked.connect(self._add_balance_by_prod_row)
        prod_layout.addLayout(self.balance_by_prod_layout)
        prod_layout.addWidget(add_by_prod_btn)
        layout.addWidget(prod_group)

        return scroll_area

    def _create_source_categories_widget(self):
        scroll_area, layout = self._create_scrollable_widget()
        
        cat1_group = QGroupBox("Стационарное сжигание (Категория 1)")
        self.source_cat1_layout = QVBoxLayout(cat1_group)
        add_cat1_btn = QPushButton("Добавить топливо")
        add_cat1_btn.clicked.connect(self._add_source_cat1_row)
        self.source_cat1_layout.addWidget(add_cat1_btn)
        layout.addWidget(cat1_group)

        cat2_group = QGroupBox("Сжигание в факелах (Категория 2)")
        self.source_cat2_layout = QVBoxLayout(cat2_group)
        add_cat2_btn = QPushButton("Добавить газ")
        add_cat2_btn.clicked.connect(self._add_source_cat2_row)
        self.source_cat2_layout.addWidget(add_cat2_btn)
        layout.addWidget(cat2_group)
        
        cat3_group = QGroupBox("Фугитивные выбросы (Категория 3)")
        self.source_cat3_layout = QVBoxLayout(cat3_group)
        add_cat3_btn = QPushButton("Добавить газ")
        add_cat3_btn.clicked.connect(self._add_source_cat3_row)
        self.source_cat3_layout.addWidget(add_cat3_btn)
        layout.addWidget(cat3_group)

        return scroll_area

    def _add_balance_raw_row(self): self._create_dynamic_row(self.balance_raw_materials, self.balance_raw_layout, self.calculator.data_service.get_petrochemical_substance_names_12_1(), [('consumption', 'Расход, т', (0.0, 1e9, 6))])
    def _add_balance_primary_row(self): self._create_dynamic_row(self.balance_primary_products, self.balance_primary_layout, self.calculator.data_service.get_petrochemical_substance_names_12_1(), [('production', 'Производство, т', (0.0, 1e9, 6))])
    def _add_balance_by_prod_row(self): self._create_dynamic_row(self.balance_by_products, self.balance_by_prod_layout, self.calculator.data_service.get_petrochemical_substance_names_12_1(), [('production', 'Производство, т', (0.0, 1e9, 6))])
    
    def _add_source_cat1_row(self):
        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)
        combo = QComboBox()
        combo.addItems(self.calculator.data_service.get_fuels_table_1_1())
        consumption = QLineEdit(placeholderText="Расход")
        oxidation = QLineEdit(placeholderText="Коэф. окисления (0-1)", text="1.0")
        oxidation.setToolTip("Коэффициент полноты сгорания топлива (доля от 0 до 1).")
        remove_button = QPushButton("Удалить")
        layout.addWidget(combo); layout.addWidget(consumption); layout.addWidget(oxidation); layout.addWidget(remove_button)
        row_data = {'widget': row_widget, 'combo': combo, 'consumption': consumption, 'oxidation': oxidation}
        self.source_stationary_fuels.append(row_data)
        self.source_cat1_layout.insertWidget(self.source_cat1_layout.count() - 1, row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data, self.source_cat1_layout, self.source_stationary_fuels))

    def _add_source_cat2_row(self):
        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)
        combo = QComboBox()
        combo.addItems(self.calculator.data_service.get_flare_gas_types_table_2_1())
        consumption = QLineEdit(placeholderText="Расход")
        unit_combo = QComboBox(); unit_combo.addItems(["тонна", "тыс. м3"])
        remove_button = QPushButton("Удалить")
        layout.addWidget(combo); layout.addWidget(consumption); layout.addWidget(unit_combo); layout.addWidget(remove_button)
        row_data = {'widget': row_widget, 'combo': combo, 'consumption': consumption, 'unit': unit_combo}
        self.source_flare_gases.append(row_data)
        self.source_cat2_layout.insertWidget(self.source_cat2_layout.count() - 1, row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data, self.source_cat2_layout, self.source_flare_gases))

    def _add_source_cat3_row(self):
        self._create_dynamic_row(self.source_fugitive_gases, self.source_cat3_layout, self.calculator.data_service.get_fugitive_gas_types_table_3_1(), [('volume', 'Объем, тыс. м3', (0.0, 1e9, 6))])

    def _create_dynamic_row(self, storage, layout, items, fields):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_data = {'widget': row_widget}
        combo = QComboBox(); combo.addItems(items)
        row_layout.addWidget(combo); row_data['combo'] = combo
        for key, placeholder, params in fields:
            editor = QLineEdit(placeholderText=placeholder)
            validator = QDoubleValidator(*params, self)
            validator.setLocale(self.c_locale)
            editor.setValidator(validator)
            row_layout.addWidget(editor); row_data[key] = editor
        remove_button = QPushButton("Удалить")
        row_layout.addWidget(remove_button)
        storage.append(row_data)
        layout.insertWidget(layout.count() - 1, row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data, layout, storage))

    def _remove_row(self, row_data, layout, storage):
        row_data['widget'].deleteLater()
        layout.removeWidget(row_data['widget'])
        storage.remove(row_data)

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(',', '.')
        if not text: raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        try:
            method_index = self.method_combobox.currentIndex()
            co2_emissions = 0.0

            def collect_data(storage_list, key_name, list_name):
                items = []
                for i, row in enumerate(storage_list):
                    name = row['combo'].currentText()
                    value = self._get_float(row[key_name], f"{list_name} для '{name}' (строка {i+1})")
                    items.append({'name': name, key_name: value})
                return items

            if method_index == 0: # Метод баланса
                raw_materials = [{'name': r['combo'].currentText(), 'consumption': self._get_float(r['consumption'], 'Расход сырья')} for r in self.balance_raw_materials]
                primary_products = [{'name': r['combo'].currentText(), 'production': self._get_float(r['production'], 'Производство осн. продукции')} for r in self.balance_primary_products]
                by_products = [{'name': r['combo'].currentText(), 'production': self._get_float(r['production'], 'Производство соп. продукции')} for r in self.balance_by_products]
                if not raw_materials: raise ValueError("Добавьте сырье.")
                co2_emissions = self.calculator.calculate_emissions_by_balance(raw_materials, primary_products, by_products)

            elif method_index == 1: # Метод по категориям
                stationary_fuels = [{'fuel_name': r['combo'].currentText(), 'fuel_consumption': self._get_float(r['consumption'], 'Расход топлива'), 'oxidation_factor': self._get_float(r['oxidation'], 'Коэф. окисления')} for r in self.source_stationary_fuels]
                flare_gases = [{'gas_type': r['combo'].currentText(), 'consumption': self._get_float(r['consumption'], 'Расход газа'), 'unit': r['unit'].currentText()} for r in self.source_flare_gases]
                fugitive_gases = [{'gas_type': r['combo'].currentText(), 'volume': self._get_float(r['volume'], 'Объем газа')} for r in self.source_fugitive_gases]
                co2_emissions = self.calculator.calculate_emissions_by_source_categories(stationary_fuels, flare_gases, fugitive_gases)

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            logging.error(f"Category 12 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            logging.critical(f"Category 12 Calculation - Unexpected error: {e}", exc_info=True)
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")