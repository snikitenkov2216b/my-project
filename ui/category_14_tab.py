# ui/category_14_tab.py - Виджет вкладки для расчетов по Категории 14.
# Реализует интерфейс для двух методов расчета в черной металлургии.
# Код написан полностью, без сокращений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_14 import Category14Calculator

class Category14Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 14 "Черная металлургия".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category14Calculator(self.data_service)
        
        self.process_raw = []
        self.process_fuels = []
        self.process_products = []
        self.process_byproducts = []
        self.enterprise_inputs = []
        self.enterprise_outputs = []
        self.enterprise_stocks = []

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Расчет по процессу (Формула 14.1)",
            "Расчет по предприятию в целом (Формула 14.2)"
        ])
        method_layout.addRow("Выберите метод расчета:", self.method_combobox)
        main_layout.addLayout(method_layout)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_process_balance_widget())
        self.stacked_widget.addWidget(self._create_enterprise_balance_widget())
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

    def _create_process_balance_widget(self):
        scroll_area, layout = self._create_scrollable_widget()

        inputs_group = QGroupBox("Входящие потоки")
        inputs_layout = QVBoxLayout(inputs_group)
        inputs_layout.addWidget(QLabel("Сырье и восстановители:"))
        self.process_raw_layout = QVBoxLayout()
        add_raw_btn = QPushButton("Добавить сырье/восстановитель")
        add_raw_btn.clicked.connect(self._add_process_raw_row)
        inputs_layout.addLayout(self.process_raw_layout)
        inputs_layout.addWidget(add_raw_btn)
        inputs_layout.addWidget(QLabel("Топливо:"))
        self.process_fuels_layout = QVBoxLayout()
        add_fuel_btn = QPushButton("Добавить топливо")
        add_fuel_btn.clicked.connect(self._add_process_fuel_row)
        inputs_layout.addLayout(self.process_fuels_layout)
        inputs_layout.addWidget(add_fuel_btn)
        layout.addWidget(inputs_group)

        outputs_group = QGroupBox("Выходящие потоки")
        outputs_layout = QVBoxLayout(outputs_group)
        outputs_layout.addWidget(QLabel("Основная продукция:"))
        self.process_products_layout = QVBoxLayout()
        add_prod_btn = QPushButton("Добавить основную продукцию")
        add_prod_btn.clicked.connect(self._add_process_product_row)
        outputs_layout.addLayout(self.process_products_layout)
        outputs_layout.addWidget(add_prod_btn)
        outputs_layout.addWidget(QLabel("Сопутствующая продукция/отходы:"))
        self.process_byproducts_layout = QVBoxLayout()
        add_byprod_btn = QPushButton("Добавить сопутствующую продукцию")
        add_byprod_btn.clicked.connect(self._add_process_byproduct_row)
        outputs_layout.addLayout(self.process_byproducts_layout)
        outputs_layout.addWidget(add_byprod_btn)
        layout.addWidget(outputs_group)
        
        return scroll_area

    def _create_enterprise_balance_widget(self):
        scroll_area, layout = self._create_scrollable_widget()

        inputs_group = QGroupBox("Входящие потоки на предприятие")
        self.enterprise_inputs_layout = QVBoxLayout(inputs_group)
        add_input_btn = QPushButton("Добавить входящий поток")
        add_input_btn.clicked.connect(self._add_enterprise_input_row)
        self.enterprise_inputs_layout.addWidget(add_input_btn)
        layout.addWidget(inputs_group)

        outputs_group = QGroupBox("Выходящие потоки с предприятия")
        self.enterprise_outputs_layout = QVBoxLayout(outputs_group)
        add_output_btn = QPushButton("Добавить выходящий поток")
        add_output_btn.clicked.connect(self._add_enterprise_output_row)
        self.enterprise_outputs_layout.addWidget(add_output_btn)
        layout.addWidget(outputs_group)
        
        stocks_group = QGroupBox("Изменение запасов на предприятии")
        self.enterprise_stocks_layout = QVBoxLayout(stocks_group)
        add_stock_btn = QPushButton("Добавить изменение запаса")
        add_stock_btn.clicked.connect(self._add_enterprise_stock_row)
        self.enterprise_stocks_layout.addWidget(add_stock_btn)
        layout.addWidget(stocks_group)
        
        return scroll_area

    def _get_all_materials(self):
        materials = self.data_service.get_metallurgy_material_names_14_1()
        fuels = self.data_service.get_fuels_table_1_1()
        return sorted(list(set(materials + fuels)))

    def _add_process_raw_row(self): self._create_dynamic_row(self.process_raw, self.process_raw_layout, self._get_all_materials(), [('consumption', 'Расход, т', (0.0, 1e9, 6))])
    def _add_process_fuel_row(self): self._create_dynamic_row(self.process_fuels, self.process_fuels_layout, self._get_all_materials(), [('consumption', 'Расход', (0.0, 1e9, 6))])
    def _add_process_product_row(self): self._create_dynamic_row(self.process_products, self.process_products_layout, self._get_all_materials(), [('production', 'Производство, т', (0.0, 1e9, 6))])
    def _add_process_byproduct_row(self): self._create_dynamic_row(self.process_byproducts, self.process_byproducts_layout, self._get_all_materials(), [('production', 'Выход, т', (0.0, 1e9, 6))])
    
    def _add_enterprise_input_row(self): self._create_dynamic_row(self.enterprise_inputs, self.enterprise_inputs_layout, self._get_all_materials(), [('mass', 'Масса, т', (0.0, 1e9, 6))])
    def _add_enterprise_output_row(self): self._create_dynamic_row(self.enterprise_outputs, self.enterprise_outputs_layout, self._get_all_materials(), [('mass', 'Масса, т', (0.0, 1e9, 6))])
    def _add_enterprise_stock_row(self): self._create_dynamic_row(self.enterprise_stocks, self.enterprise_stocks_layout, self._get_all_materials(), [('mass_change', 'Изменение массы, т', (-1e9, 1e9, 6))])

    def _create_dynamic_row(self, storage, layout, items, fields):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_data = {'widget': row_widget}
        combo = QComboBox(); combo.addItems(items)
        row_layout.addWidget(combo); row_data['combo'] = combo
        for key, placeholder, params in fields:
            editor = QLineEdit(placeholderText=placeholder)
            editor.setValidator(QDoubleValidator(*params, self))
            editor.validator().setLocale(self.c_locale)
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

            if method_index == 0: # Расчет по процессу
                raw_materials = [{'name': r['combo'].currentText(), 'consumption': self._get_float(r['consumption'], 'Расход сырья')} for r in self.process_raw]
                fuels = [{'name': r['combo'].currentText(), 'consumption': self._get_float(r['consumption'], 'Расход топлива')} for r in self.process_fuels]
                products = [{'name': r['combo'].currentText(), 'production': self._get_float(r['production'], 'Производство продукции')} for r in self.process_products]
                by_products = [{'name': r['combo'].currentText(), 'production': self._get_float(r['production'], 'Выход побочной продукции')} for r in self.process_byproducts]
                if not raw_materials and not fuels: raise ValueError("Добавьте хотя бы один входящий поток.")
                co2_emissions = self.calculator.calculate_emissions_by_process(raw_materials, fuels, products, by_products)

            elif method_index == 1: # Расчет по предприятию
                inputs = [{'name': r['combo'].currentText(), 'mass': self._get_float(r['mass'], 'Масса вх. потока')} for r in self.enterprise_inputs]
                outputs = [{'name': r['combo'].currentText(), 'mass': self._get_float(r['mass'], 'Масса вых. потока')} for r in self.enterprise_outputs]
                stock_changes = [{'name': r['combo'].currentText(), 'mass_change': self._get_float(r['mass_change'], 'Изменение запаса')} for r in self.enterprise_stocks]
                if not inputs: raise ValueError("Добавьте хотя бы один входящий поток.")
                co2_emissions = self.calculator.calculate_emissions_by_enterprise_balance(inputs, outputs, stock_changes)

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")