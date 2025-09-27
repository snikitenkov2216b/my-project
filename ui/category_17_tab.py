# ui/category_17_tab.py - Виджет вкладки для расчетов по Категории 17.
# Реализует интерфейс для различных промышленных процессов.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QGroupBox, QHBoxLayout
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt

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

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.calc_type_combobox = QComboBox()
        self.calc_type_combobox.addItems([
            "Неэнергетическое использование топлива",
            "Использование восстановителей",
            "Использование карбонатов"
        ])
        main_layout.addWidget(QLabel("Выберите тип процесса:"))
        main_layout.addWidget(self.calc_type_combobox)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_fuel_use_widget())
        self.stacked_widget.addWidget(self._create_reductants_widget())
        self.stacked_widget.addWidget(self._create_carbonates_widget())
        main_layout.addWidget(self.stacked_widget)

        self.calc_type_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)

        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_fuel_use_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        fuels_group = QGroupBox("Топливо")
        self.fuels_layout = QVBoxLayout()
        add_fuel_button = QPushButton("Добавить топливо")
        add_fuel_button.clicked.connect(self._add_fuel_use_fuel_row)
        fuels_group.setLayout(self.fuels_layout)
        layout.addWidget(fuels_group)
        layout.addWidget(add_fuel_button)

        products_group = QGroupBox("Продукция")
        self.products_layout = QVBoxLayout()
        add_product_button = QPushButton("Добавить продукт")
        add_product_button.clicked.connect(self._add_fuel_use_product_row)
        products_group.setLayout(self.products_layout)
        layout.addWidget(products_group)
        layout.addWidget(add_product_button)
        
        return widget

    def _create_reductants_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Восстановители")
        self.reductants_layout = QVBoxLayout()
        add_button = QPushButton("Добавить восстановитель")
        add_button.clicked.connect(self._add_reductant_row)
        group.setLayout(self.reductants_layout)
        layout.addWidget(group)
        layout.addWidget(add_button)
        return widget

    def _create_carbonates_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Карбонаты")
        self.carbonates_layout = QVBoxLayout()
        add_button = QPushButton("Добавить карбонат")
        add_button.clicked.connect(self._add_carbonate_row)
        group.setLayout(self.carbonates_layout)
        layout.addWidget(group)
        layout.addWidget(add_button)
        return widget

    def _create_dynamic_row(self, placeholder, target_layout, storage, item_list):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        combo = QComboBox()
        combo.addItems(item_list)
        line_edit = QLineEdit(placeholderText=placeholder)
        line_edit.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        remove_button = QPushButton("Удалить")
        row_layout.addWidget(combo)
        row_layout.addWidget(line_edit)
        row_layout.addWidget(remove_button)
        row_data = {'widget': row_widget, 'combo': combo, 'input': line_edit}
        storage.append(row_data)
        target_layout.addWidget(row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data, target_layout, storage))

    def _remove_row(self, row_data, layout, storage):
        row_data['widget'].deleteLater()
        layout.removeWidget(row_data['widget'])
        storage.remove(row_data)

    def _add_fuel_use_fuel_row(self):
        self._create_dynamic_row("Расход, т", self.fuels_layout, self.fuel_use_fuels, self.data_service.get_fuels_table_1_1())
        
    def _add_fuel_use_product_row(self):
        self._create_dynamic_row("Выход, т", self.products_layout, self.fuel_use_products, self.data_service.get_fuels_table_1_1())

    def _add_reductant_row(self):
        self._create_dynamic_row("Расход, т", self.reductants_layout, self.reductants, self.data_service.get_fuels_table_1_1())

    def _add_carbonate_row(self):
        items = self.data_service.get_carbonate_formulas_table_6_1() + self.data_service.get_glass_carbonate_formulas_table_8_1()
        self._create_dynamic_row("Масса, т", self.carbonates_layout, self.carbonates, sorted(list(set(items))))

    def _perform_calculation(self):
        try:
            current_index = self.calc_type_combobox.currentIndex()
            co2_emissions = 0.0

            if current_index == 0:
                fuels = [{'name': r['combo'].currentText(), 'consumption': float(r['input'].text().replace(',', '.'))} for r in self.fuel_use_fuels if r['input'].text()]
                products = [{'name': r['combo'].currentText(), 'production': float(r['input'].text().replace(',', '.'))} for r in self.fuel_use_products if r['input'].text()]
                if not fuels: raise ValueError("Добавьте хотя бы один вид топлива.")
                co2_emissions = self.calculator.calculate_from_fuel_use(fuels, products)
            
            elif current_index == 1:
                reductants = [{'name': r['combo'].currentText(), 'consumption': float(r['input'].text().replace(',', '.'))} for r in self.reductants if r['input'].text()]
                if not reductants: raise ValueError("Добавьте хотя бы один восстановитель.")
                co2_emissions = self.calculator.calculate_from_reductants(reductants)

            elif current_index == 2:
                carbonates = [{'name': r['combo'].currentText(), 'mass': float(r['input'].text().replace(',', '.'))} for r in self.carbonates if r['input'].text()]
                if not carbonates: raise ValueError("Добавьте хотя бы один карбонат.")
                co2_emissions = self.calculator.calculate_from_carbonates(carbonates)
            
            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")