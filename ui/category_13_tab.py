# ui/category_13_tab.py - Виджет вкладки для расчетов по Категории 13.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale # <--- ДОБАВЛЕН ИМПОРТ QLocale

from data_models import DataService
from calculations.category_13 import Category13Calculator

class Category13Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 13 "Производство фторсодержащих веществ".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category13Calculator(self.data_service)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Создаем локаль, которая использует точку как разделитель
        c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

        # 1. Выбор парникового газа
        self.gas_combobox = QComboBox()
        self.gas_combobox.addItems(["CHF3 (из производства ГХФУ-22)", "SF6 (из производства SF6)"])
        form_layout.addRow("Парниковый газ:", self.gas_combobox)

        # 2. Поле для ввода массы произведенной продукции
        self.production_input = QLineEdit()
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        prod_validator = QDoubleValidator(0.0, 1e9, 6, self)
        prod_validator.setLocale(c_locale)
        self.production_input.setValidator(prod_validator)
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
        self.production_input.setPlaceholderText("Масса основной продукции, т")
        form_layout.addRow("Производство продукции:", self.production_input)
        
        # 3. Поле для ввода коэффициента выбросов
        self.emission_factor_input = QLineEdit()
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        ef_validator = QDoubleValidator(0.0, 1e9, 6, self)
        ef_validator.setLocale(c_locale)
        self.emission_factor_input.setValidator(ef_validator)
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
        self.emission_factor_input.setPlaceholderText("кг/т основной продукции")
        form_layout.addRow("Коэффициент выбросов:", self.emission_factor_input)

        main_layout.addLayout(form_layout)

        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _perform_calculation(self):
        try:
            production_str = self.production_input.text().replace(',', '.')
            ef_str = self.emission_factor_input.text().replace(',', '.')

            if not production_str or not ef_str:
                raise ValueError("Пожалуйста, заполните все поля.")
            
            production_mass = float(production_str)
            emission_factor = float(ef_str)
            
            emissions = self.calculator.calculate_emissions(production_mass, emission_factor)
            
            gas_name = "CHF3" if self.gas_combobox.currentIndex() == 0 else "SF6"
            self.result_label.setText(f"Результат: {emissions:.4f} тонн {gas_name}")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")