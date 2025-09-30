# ui/category_3_tab.py - Виджет вкладки для расчетов по Категории 3.
# Код полностью реализует интерфейс для расчета фугитивных выбросов.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox,
    QLineEdit, QPushButton, QLabel, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_3 import Category3Calculator

class Category3Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 3 "Фугитивные выбросы".
    """
    def __init__(self, data_service: DataService, parent=None):
        """
        Конструктор вкладки.
        
        :param data_service: Экземпляр сервиса для доступа к данным.
        :param parent: Родительский виджет.
        """
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category3Calculator(self.data_service)
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        """
        Инициализирует все элементы пользовательского интерфейса на вкладке.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 1. Выпадающий список для выбора вида углеводородной смеси
        self.gas_type_combobox = QComboBox()
        gas_types = self.data_service.get_fugitive_gas_types_table_3_1()
        self.gas_type_combobox.addItems(gas_types)
        form_layout.addRow("Вид углеводородной смеси:", self.gas_type_combobox)

        # 2. Поле для ввода объема отведения (стравливания)
        volume_layout = QHBoxLayout()
        self.volume_input = QLineEdit()
        
        # ИСПРАВЛЕНО
        volume_validator = QDoubleValidator(0.0, 1e12, 6, self)
        volume_validator.setLocale(self.c_locale)
        self.volume_input.setValidator(volume_validator)
        self.volume_input.setPlaceholderText("Введите числовое значение")
        
        volume_layout.addWidget(self.volume_input)
        volume_layout.addWidget(QLabel("(тыс. м³)"))
        form_layout.addRow("Объем отведения смеси:", volume_layout)

        main_layout.addLayout(form_layout)

        # 3. Кнопка расчета
        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        # 4. Метка для вывода результата
        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _get_float_from_input(self, line_edit, field_name):
        """Вспомогательная функция для получения числового значения из поля ввода."""
        text = line_edit.text().replace(',', '.')
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        """
        Выполняет расчет при нажатии на кнопку.
        """
        try:
            gas_type = self.gas_type_combobox.currentText()
            volume = self._get_float_from_input(self.volume_input, "Объем отведения смеси")

            emissions = self.calculator.calculate_emissions(
                gas_type=gas_type,
                volume=volume
            )

            co2 = emissions.get('co2', 0.0)
            ch4 = emissions.get('ch4', 0.0)
            self.result_label.setText(f"Результат: {co2:.4f} тонн CO2, {ch4:.4f} тонн CH4")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")