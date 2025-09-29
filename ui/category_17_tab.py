# ui/category_17_tab.py - Виджет вкладки для расчетов по Категории 17.
# Реализует интерфейс для прочих промышленных процессов.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_17 import Category17Calculator

class Category17Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 17 "Прочие промышленные процессы".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category17Calculator(self.data_service)
        
        self.fuel_use_fuels = []
        self.fuel_use_products = []
        self.reductants = []
        self.carbonates = []

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Выбор метода ---
        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Неэнергетическое использование топлива (Формула 17.1)",
            "Использование восстановителей (Формула 17.2)",
            "Использование карбонатов (Формула 17.3)"
        ])
        method_layout.addRow("Выберите тип процесса/расчета:", self.method_combobox)
        main_layout.addLayout(method_layout)
        
        # --- Стек виджетов ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_fuel_use_widget())
        self.stacked_widget.addWidget(self._create_reductants_widget())
        self.stacked_widget.addWidget(self._create_carbonates_widget())
        main_layout.addWidget(self.stacked_widget)
        
        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_fuel_use_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        fuels_group = QGroupBox("Использованное топливо")
        self.fuel_use_fuels_layout = QVBoxLayout(fuels_group)
        add_fuel_btn = QPushButton("Добавить топливо")
        add_fuel_btn.clicked.connect(self._add_fuel_use_fuel_row)
        layout.addWidget(fuels_group)
        layout.addWidget(add_fuel_btn)

        products_group = QGroupBox("Продукция, в которой связан углерод")
        self.fuel_use_products_layout = QVBoxLayout(products_group)
        add_product_btn = QPushButton("Добавить продукцию")
        add_product_btn.clicked.connect(self._add_fuel_use_product_row)
        layout.addWidget(products_group)
        layout.addWidget(add_product_btn)

        scroll_area.setWidget(widget)
        return scroll_area

    def _create_reductants_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Использованные восстановители")
        self.reductants_layout = QVBoxLayout(group)
        add_btn = QPushButton("Добавить восстановитель")
        add_btn.clicked.connect(self._add_reductant_row)
        layout.addWidget(group)
        layout.addWidget(add_btn)
        return widget

    def _create_carbonates_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Использованные карбонаты")
        self.carbonates_layout = QVBoxLayout(group)
        add_btn = QPushButton("Добавить карбонат")
        add_btn.clicked.connect(self._add_carbonate_row)
        layout.addWidget(group)
        layout.addWidget(add_btn)
        return widget

    # --- Методы для добавления/удаления строк ---
    def _add_fuel_use_fuel_row(self):
        items = self.data_service.get_fuels_table_1_1()
        self._create_dynamic_row("Расход", self.fuel_use_fuels_layout, self.fuel_use_fuels, items)

    def _add_fuel_use_product_row(self):
        items = self.data_service.get_fuels_table_1_1() # Продукты часто те же, что и топливо
        self._create_dynamic_row("Производство, т", self.fuel_use_products_layout, self.fuel_use_products, items)

    def _add_reductant_row(self):
        items = self.data_service.get_fuels_table_1_1() # Восстановители - это виды топлива
        self._create_dynamic_row("Расход, т", self.reductants_layout, self.reductants, items)

    def _add_carbonate_row(self):
        items = self.data_service.get_carbonate_formulas_table_6_1()
        self._create_dynamic_row("Масса, т", self.carbonates_layout, self.carbonates, items)

    def _create_dynamic_row(self, placeholder, layout, storage, items):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        combo = QComboBox()
        combo.addItems(items)
        line_edit = QLineEdit(placeholderText=placeholder)
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        line_edit.setValidator(validator)
        remove_button = QPushButton("Удалить")
        row_layout.addWidget(combo)
        row_layout.addWidget(line_edit)
        row_layout.addWidget(remove_button)
        row_data = {'widget': row_widget, 'combo': combo, 'input': line_edit}
        storage.append(row_data)
        layout.addWidget(row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data, layout, storage))

    def _remove_row(self, row_data, layout, storage):
        row_widget = row_data['widget']
        layout.removeWidget(row_widget)
        row_widget.deleteLater()
        storage.remove(row_data)

    def _perform_calculation(self):
        try:
            method_index = self.method_combobox.currentIndex()
            co2_emissions = 0.0

            if method_index == 0: # Неэнергетическое использование
                def collect_data(storage_list, key_name):
                    items = []
                    for row in storage_list:
                        name = row['combo'].currentText()
                        value_str = row['input'].text().replace(',', '.')
                        if not value_str: raise ValueError(f"Не заполнено поле для '{name}'")
                        items.append({'name': name, key_name: float(value_str)})
                    return items
                fuels = collect_data(self.fuel_use_fuels, 'consumption')
                products = collect_data(self.fuel_use_products, 'production')
                if not fuels: raise ValueError("Добавьте хотя бы один вид топлива.")
                co2_emissions = self.calculator.calculate_from_fuel_use(fuels, products)

            elif method_index == 1: # Восстановители
                reductants_data = []
                for row in self.reductants:
                    name = row['combo'].currentText()
                    value_str = row['input'].text().replace(',', '.')
                    if not value_str: raise ValueError(f"Не заполнено поле для '{name}'")
                    reductants_data.append({'name': name, 'consumption': float(value_str)})
                if not reductants_data: raise ValueError("Добавьте хотя бы один восстановитель.")
                co2_emissions = self.calculator.calculate_from_reductants(reductants_data)
            
            elif method_index == 2: # Карбонаты
                carbonates_data = []
                for row in self.carbonates:
                    name = row['combo'].currentText()
                    value_str = row['input'].text().replace(',', '.')
                    if not value_str: raise ValueError(f"Не заполнено поле для '{name}'")
                    carbonates_data.append({'name': name, 'mass': float(value_str)})
                if not carbonates_data: raise ValueError("Добавьте хотя бы один карбонат.")
                co2_emissions = self.calculator.calculate_from_carbonates(carbonates_data)

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")