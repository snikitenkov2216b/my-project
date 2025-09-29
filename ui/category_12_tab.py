# ui/category_12_tab.py - Виджет вкладки для расчетов по Категории 12.
# Реализует интерфейс для двух методов расчета в нефтехимическом производстве.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_12 import Category12Calculator

class Category12Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 12 "Нефтехимическое производство".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category12Calculator(self.data_service)
        
        # Списки для хранения динамических строк
        self.balance_raw_materials = []
        self.balance_primary_products = []
        self.balance_by_products = []
        self.source_stationary = []
        self.source_flare = []
        self.source_fugitive = []

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Выбор метода ---
        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Метод углеродного баланса (Формула 12.1)",
            "Метод по категориям источников (Формула 12.2)"
        ])
        method_layout.addRow("Выберите метод расчета:", self.method_combobox)
        main_layout.addLayout(method_layout)
        
        # --- Стек виджетов ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_balance_widget())
        self.stacked_widget.addWidget(self._create_source_categories_widget())
        main_layout.addWidget(self.stacked_widget)
        
        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_balance_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Сырье
        raw_group = QGroupBox("Сырье (входящий поток)")
        self.balance_raw_layout = QVBoxLayout()
        raw_group.setLayout(self.balance_raw_layout)
        add_raw_btn = QPushButton("Добавить сырье")
        add_raw_btn.clicked.connect(self._add_balance_raw_row)
        layout.addWidget(raw_group)
        layout.addWidget(add_raw_btn)

        # Продукция
        prod_group = QGroupBox("Продукция (выходящий поток)")
        prod_layout = QVBoxLayout(prod_group)
        self.balance_primary_layout = QVBoxLayout()
        self.balance_by_prod_layout = QVBoxLayout()
        add_primary_btn = QPushButton("Добавить основную продукцию")
        add_by_prod_btn = QPushButton("Добавить сопутствующую продукцию")
        add_primary_btn.clicked.connect(self._add_balance_primary_row)
        add_by_prod_btn.clicked.connect(self._add_balance_by_prod_row)
        prod_layout.addWidget(QLabel("Основная продукция:"))
        prod_layout.addLayout(self.balance_primary_layout)
        prod_layout.addWidget(add_primary_btn)
        prod_layout.addWidget(QLabel("Сопутствующая продукция:"))
        prod_layout.addLayout(self.balance_by_prod_layout)
        prod_layout.addWidget(add_by_prod_btn)
        layout.addWidget(prod_group)

        scroll_area.setWidget(widget)
        return scroll_area

    def _create_source_categories_widget(self):
        # Этот виджет будет содержать упрощенные формы для Категорий 1, 2, 3
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # ... (реализация интерфейса для метода по категориям источников)
        layout.addWidget(QLabel("Интерфейс для этого метода в разработке."))
        return widget

    def _add_balance_raw_row(self):
        items = self.data_service.get_petrochemical_substance_names_12_1()
        self._create_dynamic_row("Расход, т", self.balance_raw_layout, self.balance_raw_materials, items)

    def _add_balance_primary_row(self):
        items = self.data_service.get_petrochemical_substance_names_12_1()
        self._create_dynamic_row("Производство, т", self.balance_primary_layout, self.balance_primary_products, items)

    def _add_balance_by_prod_row(self):
        items = self.data_service.get_petrochemical_substance_names_12_1()
        self._create_dynamic_row("Производство, т", self.balance_by_prod_layout, self.balance_by_products, items)
        
    def _create_dynamic_row(self, placeholder: str, layout: QVBoxLayout, storage: list, items: list):
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

            if method_index == 0: # Метод баланса
                def collect_data(storage_list, key_name):
                    items = []
                    for row in storage_list:
                        name = row['combo'].currentText()
                        value_str = row['input'].text().replace(',', '.')
                        if not value_str: raise ValueError(f"Не заполнено поле для '{name}'")
                        items.append({'name': name, key_name: float(value_str)})
                    return items

                raw_materials = collect_data(self.balance_raw_materials, 'consumption')
                primary_products = collect_data(self.balance_primary_products, 'production')
                by_products = collect_data(self.balance_by_products, 'production')
                
                if not raw_materials: raise ValueError("Добавьте хотя бы один вид сырья.")

                co2_emissions = self.calculator.calculate_emissions_by_balance(
                    raw_materials, primary_products, by_products
                )
            
            elif method_index == 1: # Метод по категориям
                raise NotImplementedError("Расчет по категориям источников находится в разработке.")

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except NotImplementedError as e:
            QMessageBox.information(self, "В разработке", str(e))
            self.result_label.setText("Результат:...")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")