# ui/category_5_tab.py - Виджет вкладки для расчетов по Категории 5.
# Реализует динамический интерфейс для метода углеродного баланса.
# Код написан полностью, без сокращений и упрощений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QGroupBox, QHBoxLayout, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_5 import Category5Calculator

class Category5Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 5 "Производство кокса".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category5Calculator(self.data_service)
        
        self.raw_material_rows = []
        self.fuel_rows = []
        self.by_product_rows = []

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        form_container_layout = QVBoxLayout(main_widget)
        form_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(main_widget)
        main_layout.addWidget(scroll_area)

        # --- Блок входящих потоков ---
        inputs_group = QGroupBox("Входящие потоки (Сырье и Топливо)")
        inputs_layout = QVBoxLayout(inputs_group)

        inputs_layout.addWidget(QLabel("Сырье (коксующиеся угли):"))
        self.raw_materials_layout = QVBoxLayout()
        add_raw_material_button = QPushButton("Добавить сырье")
        add_raw_material_button.clicked.connect(self._add_raw_material_row)
        inputs_layout.addLayout(self.raw_materials_layout)
        inputs_layout.addWidget(add_raw_material_button, alignment=Qt.AlignmentFlag.AlignLeft)

        inputs_layout.addWidget(QLabel("Топливо:"))
        self.fuels_layout = QVBoxLayout()
        add_fuel_button = QPushButton("Добавить топливо")
        add_fuel_button.clicked.connect(self._add_fuel_row)
        inputs_layout.addLayout(self.fuels_layout)
        inputs_layout.addWidget(add_fuel_button, alignment=Qt.AlignmentFlag.AlignLeft)
        
        form_container_layout.addWidget(inputs_group)

        # --- Блок выходящих потоков ---
        outputs_group = QGroupBox("Выходящие потоки (Продукция)")
        outputs_layout = QVBoxLayout(outputs_group)

        main_product_layout = QFormLayout()
        self.main_product_consumption = QLineEdit()
        main_product_validator = QDoubleValidator(0.0, 1e9, 6, self)
        main_product_validator.setLocale(self.c_locale)
        self.main_product_consumption.setValidator(main_product_validator)
        main_product_layout.addRow("Производство кокса (т):", self.main_product_consumption)
        outputs_layout.addLayout(main_product_layout)

        outputs_layout.addWidget(QLabel("Сопутствующая продукция и отходы:"))
        self.by_products_layout = QVBoxLayout()
        add_by_product_button = QPushButton("Добавить сопутствующий продукт")
        add_by_product_button.clicked.connect(self._add_by_product_row)
        outputs_layout.addLayout(self.by_products_layout)
        outputs_layout.addWidget(add_by_product_button, alignment=Qt.AlignmentFlag.AlignLeft)

        outputs_group.setLayout(outputs_layout)
        form_container_layout.addWidget(outputs_group)

        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        form_container_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        form_container_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_dynamic_row(self, placeholder_text: str, target_layout: QVBoxLayout, storage_list: list, item_list: list):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        
        combo = QComboBox()
        combo.addItems(item_list)
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder_text)
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        line_edit.setValidator(validator)
        
        remove_button = QPushButton("Удалить")
        
        row_layout.addWidget(combo)
        row_layout.addWidget(line_edit)
        row_layout.addWidget(remove_button)
        
        row_data = {'widget': row_widget, 'combo': combo, 'input': line_edit}
        storage_list.append(row_data)
        target_layout.addWidget(row_widget)
        
        remove_button.clicked.connect(lambda: self._remove_row(row_data, target_layout, storage_list))

    def _remove_row(self, row_data: dict, target_layout: QVBoxLayout, storage_list: list):
        row_widget = row_data['widget']
        target_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        storage_list.remove(row_data)

    def _add_raw_material_row(self):
        items = [f for f in self.data_service.get_fuels_table_1_1() if "уголь" in f.lower()]
        self._create_dynamic_row("Расход сырья, т", self.raw_materials_layout, self.raw_material_rows, items)

    def _add_fuel_row(self):
        items = self.data_service.get_fuels_table_1_1()
        self._create_dynamic_row("Расход топлива", self.fuels_layout, self.fuel_rows, items)

    def _add_by_product_row(self):
        items = self.data_service.get_fuels_table_1_1()
        self._create_dynamic_row("Выход продукта", self.by_products_layout, self.by_product_rows, items)

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(',', '.')
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        try:
            def collect_data(storage_list, key_name, list_name):
                items = []
                for i, row in enumerate(storage_list):
                    name = row['combo'].currentText()
                    value = self._get_float(row['input'], f"{list_name}, строка {i+1}")
                    items.append({'name': name, key_name: value})
                return items

            raw_materials = collect_data(self.raw_material_rows, 'consumption', "Сырье")
            fuels = collect_data(self.fuel_rows, 'consumption', "Топливо")
            by_products = collect_data(self.by_product_rows, 'production', "Сопутствующая продукция")
            
            if not raw_materials:
                raise ValueError("Добавьте хотя бы один вид сырья.")

            main_prod_value = self._get_float(self.main_product_consumption, "Производство кокса")
            main_product = {
                'name': 'Кокс металлургический',
                'production': main_prod_value
            }

            co2_emissions = self.calculator.calculate_emissions(
                raw_materials, fuels, main_product, by_products
            )

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")