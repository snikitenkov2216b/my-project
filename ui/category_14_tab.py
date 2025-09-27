# ui/category_14_tab.py - Виджет вкладки для расчетов по Категории 14.
# Реализует динамический интерфейс для метода углеродного баланса в черной металлургии.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QGroupBox, QHBoxLayout, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt

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
        
        self.raw_material_rows = []
        self.fuel_rows = []
        self.product_rows = []
        self.by_product_rows = []

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

        # --- Входящие потоки ---
        inputs_group = QGroupBox("Входящие потоки")
        inputs_layout = QVBoxLayout()
        
        inputs_layout.addWidget(QLabel("Сырье, материалы, восстановители:"))
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
        
        inputs_group.setLayout(inputs_layout)
        form_container_layout.addWidget(inputs_group)

        # --- Выходящие потоки ---
        outputs_group = QGroupBox("Выходящие потоки")
        outputs_layout = QVBoxLayout()

        outputs_layout.addWidget(QLabel("Основная продукция:"))
        self.products_layout = QVBoxLayout()
        add_product_button = QPushButton("Добавить основную продукцию")
        add_product_button.clicked.connect(self._add_product_row)
        outputs_layout.addLayout(self.products_layout)
        outputs_layout.addWidget(add_product_button, alignment=Qt.AlignmentFlag.AlignLeft)

        outputs_layout.addWidget(QLabel("Сопутствующая продукция и отходы:"))
        self.by_products_layout = QVBoxLayout()
        add_by_product_button = QPushButton("Добавить сопутствующий продукт")
        add_by_product_button.clicked.connect(self._add_by_product_row)
        outputs_layout.addLayout(self.by_products_layout)
        outputs_layout.addWidget(add_by_product_button, alignment=Qt.AlignmentFlag.AlignLeft)

        outputs_group.setLayout(outputs_layout)
        form_container_layout.addWidget(outputs_group)

        # --- Кнопка расчета и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        form_container_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        form_container_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_dynamic_row(self, placeholder_text, target_layout, storage_list, item_list):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        
        combo = QComboBox()
        combo.addItems(item_list)
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder_text)
        line_edit.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        
        remove_button = QPushButton("Удалить")
        
        row_layout.addWidget(combo)
        row_layout.addWidget(line_edit)
        row_layout.addWidget(remove_button)
        
        row_data = {'widget': row_widget, 'combo': combo, 'input': line_edit}
        storage_list.append(row_data)
        target_layout.addWidget(row_widget)
        
        remove_button.clicked.connect(lambda: self._remove_row(row_data, target_layout, storage_list))

    def _remove_row(self, row_data, target_layout, storage_list):
        row_widget = row_data['widget']
        target_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        storage_list.remove(row_data)

    def _add_raw_material_row(self):
        items = self.data_service.get_metallurgy_material_names_table_14_1() + self.data_service.get_fuels_table_1_1()
        self._create_dynamic_row("Расход, т", self.raw_materials_layout, self.raw_material_rows, sorted(list(set(items))))

    def _add_fuel_row(self):
        items = self.data_service.get_fuels_table_1_1()
        self._create_dynamic_row("Расход, т или тыс. м3", self.fuels_layout, self.fuel_rows, items)

    def _add_product_row(self):
        items = self.data_service.get_metallurgy_material_names_table_14_1() + self.data_service.get_fuels_table_1_1()
        self._create_dynamic_row("Выход, т", self.products_layout, self.product_rows, sorted(list(set(items))))

    def _add_by_product_row(self):
        items = self.data_service.get_metallurgy_material_names_table_14_1() + self.data_service.get_fuels_table_1_1()
        self._create_dynamic_row("Выход, т или тыс. м3", self.by_products_layout, self.by_product_rows, sorted(list(set(items))))

    def _perform_calculation(self):
        try:
            def collect_data(storage_list, key_name):
                items = []
                for row in storage_list:
                    name = row['combo'].currentText()
                    value_str = row['input'].text().replace(',', '.')
                    if not value_str:
                        raise ValueError(f"Не заполнено поле для '{name}'")
                    items.append({'name': name, key_name: float(value_str)})
                return items

            raw_materials = collect_data(self.raw_material_rows, 'consumption')
            fuels = collect_data(self.fuel_rows, 'consumption')
            products = collect_data(self.product_rows, 'production')
            by_products = collect_data(self.by_product_rows, 'production')

            if not raw_materials and not fuels and not products and not by_products:
                raise ValueError("Необходимо добавить хотя бы один материальный поток.")

            co2_emissions = self.calculator.calculate_emissions(
                raw_materials, fuels, products, by_products
            )

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")