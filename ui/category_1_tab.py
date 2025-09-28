# ui/category_1_tab.py - Виджет вкладки для расчетов по Категории 1.
# Этот модуль отвечает за создание пользовательского интерфейса для
# ввода данных и отображения результатов по стационарному сжиганию топлива.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox,
    QLineEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale # <--- ДОБАВЛЕН ИМПОРТ QLocale

# Импортируем сервисы данных и логики
from data_models import DataService
from calculations.category_1 import Category1Calculator

class Category1Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 1 "Стационарное сжигание топлива".
    """
    def __init__(self, data_service: DataService, parent=None):
        """
        Конструктор вкладки.
        
        :param data_service: Экземпляр сервиса для доступа к данным.
        :param parent: Родительский виджет.
        """
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category1Calculator(self.data_service)

        # Инициализация пользовательского интерфейса
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

        # --- ОБЩЕЕ ИСПРАВЛЕНИЕ ДЛЯ ВСЕХ ФАЙЛОВ UI ---
        # Создаем локаль, которая использует точку как разделитель
        c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        # --- КОНЕЦ ОБЩЕГО ИСПРАВЛЕНИЯ ---

        self.fuel_combobox = QComboBox()
        fuels = self.data_service.get_fuels_table_1_1()
        self.fuel_combobox.addItems(fuels)
        self.fuel_combobox.currentIndexChanged.connect(self._update_units)
        form_layout.addRow("Вид топлива:", self.fuel_combobox)

        consumption_layout = QHBoxLayout()
        self.fuel_consumption_input = QLineEdit()
        
        # Применяем валидатор с исправленной локалью
        consumption_validator = QDoubleValidator(0.0, 1e9, 6, self)
        consumption_validator.setLocale(c_locale)
        self.fuel_consumption_input.setValidator(consumption_validator)
        self.fuel_consumption_input.setPlaceholderText("Введите числовое значение")
        
        self.units_label = QLabel()
        consumption_layout.addWidget(self.fuel_consumption_input)
        consumption_layout.addWidget(self.units_label)
        form_layout.addRow("Расход топлива:", consumption_layout)

        self.oxidation_factor_input = QLineEdit()
        
        # Применяем валидатор с исправленной локалью
        oxidation_validator = QDoubleValidator(0.0, 1.0, 4, self)
        oxidation_validator.setLocale(c_locale)
        self.oxidation_factor_input.setValidator(oxidation_validator)
        
        self.oxidation_factor_input.setText("1.0")
        self.oxidation_factor_input.setToolTip(
            "Доля окисленного углерода. Для газа и жидкости = 1.0. \n"
            "Для твердого топлива может быть иным. \n"
            "Для рядовых углей из таблицы 1.1 принимается равным 1."
        )
        form_layout.addRow("Коэффициент окисления (0-1):", self.oxidation_factor_input)

        main_layout.addLayout(form_layout)

        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self._update_units()

    def _update_units(self):
        """
        Обновляет метку с единицами измерения в зависимости от выбранного топлива.
        """
        selected_fuel = self.fuel_combobox.currentText()
        fuel_data = self.data_service.get_fuel_data_table_1_1(selected_fuel)
        if fuel_data and 'unit' in fuel_data:
            self.units_label.setText(f"({fuel_data['unit']})")
        else:
            self.units_label.setText("")

    def _perform_calculation(self):
        """
        Выполняет расчет при нажатии на кнопку.
        """
        try:
            fuel_name = self.fuel_combobox.currentText()
            
            consumption_str = self.fuel_consumption_input.text().replace(',', '.')
            oxidation_str = self.oxidation_factor_input.text().replace(',', '.')

            if not consumption_str or not oxidation_str:
                raise ValueError("Пожалуйста, заполните все поля.")

            fuel_consumption = float(consumption_str)
            oxidation_factor = float(oxidation_str)

            co2_emissions = self.calculator.calculate_co2_emissions(
                fuel_name=fuel_name,
                fuel_consumption=fuel_consumption,
                oxidation_factor=oxidation_factor
            )

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")