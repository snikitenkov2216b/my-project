# ui/category_21_tab.py - Виджет вкладки для расчетов по Категории 21.
# Реализует интерфейс для биологической переработки твердых отходов.
# Код написан полностью, без сокращений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_21 import Category21Calculator

class Category21Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 21 "Биологическая переработка твердых отходов".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category21Calculator(self.data_service)
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        """Инициализирует все элементы пользовательского интерфейса на вкладке."""
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        form_layout = QFormLayout()

        # Выбор типа переработки
        self.treatment_type_combobox = QComboBox()
        treatment_types = self.data_service.get_biological_treatment_types_table_21_1()
        self.treatment_type_combobox.addItems(treatment_types)
        form_layout.addRow("Тип переработки:", self.treatment_type_combobox)
        
        # Ввод массы отходов
        self.waste_mass_input = QLineEdit()
        # ИСПРАВЛЕНО
        waste_validator = QDoubleValidator(0.0, 1e9, 6, self)
        waste_validator.setLocale(self.c_locale)
        self.waste_mass_input.setValidator(waste_validator)
        form_layout.addRow("Масса отходов (тонн, сырой вес):", self.waste_mass_input)
        
        # Ввод рекуперированного метана
        self.recovered_ch4_input = QLineEdit("0.0")
        # ИСПРАВЛЕНО
        recovered_validator = QDoubleValidator(0.0, 1e9, 6, self)
        recovered_validator.setLocale(self.c_locale)
        self.recovered_ch4_input.setValidator(recovered_validator)
        form_layout.addRow("Рекуперированный CH4 (тонн, для CH4):", self.recovered_ch4_input)

        main_layout.addLayout(form_layout)

        # Кнопка расчета
        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Метка для вывода результата
        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _get_float(self, line_edit, field_name):
        """Вспомогательная функция для получения числового значения из поля ввода."""
        text = line_edit.text().replace(',', '.')
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        """Выполняет расчет на основе введенных данных."""
        try:
            treatment_type = self.treatment_type_combobox.currentText()
            waste_mass = self._get_float(self.waste_mass_input, "Масса отходов")
            recovered_ch4 = self._get_float(self.recovered_ch4_input, "Рекуперированный CH4")

            # Расчет выбросов CH4
            ch4_emissions = self.calculator.calculate_ch4_emissions(
                waste_mass=waste_mass,
                treatment_type=treatment_type,
                recovered_ch4=recovered_ch4
            )

            # Расчет выбросов N2O
            n2o_emissions = self.calculator.calculate_n2o_emissions(
                waste_mass=waste_mass,
                treatment_type=treatment_type
            )
            
            result_text = (
                f"Результат:\n"
                f"Выбросы CH4: {ch4_emissions:.4f} тонн\n"
                f"Выбросы N2O: {n2o_emissions:.4f} тонн"
            )
            self.result_label.setText(result_text)

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")