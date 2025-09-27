# ui/category_1_tab.py - Виджет вкладки для расчетов по Категории 1.
# Этот модуль отвечает за создание пользовательского интерфейса для
# ввода данных и отображения результатов по стационарному сжиганию топлива.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox,
    QLineEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt

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
        # Основной макет для всей вкладки
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Форма для ввода данных ---
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 1. Выпадающий список для выбора вида топлива
        self.fuel_combobox = QComboBox()
        fuels = self.data_service.get_fuels_table_1_1()
        self.fuel_combobox.addItems(fuels)
        self.fuel_combobox.currentIndexChanged.connect(self._update_units) # Обновление единиц при смене топлива
        form_layout.addRow("Вид топлива:", self.fuel_combobox)

        # 2. Поле для ввода расхода топлива
        consumption_layout = QHBoxLayout()
        self.fuel_consumption_input = QLineEdit()
        # Валидатор, разрешающий ввод только чисел (включая дробные)
        self.fuel_consumption_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        self.fuel_consumption_input.setPlaceholderText("Введите числовое значение")
        self.units_label = QLabel() # Метка для единиц измерения
        consumption_layout.addWidget(self.fuel_consumption_input)
        consumption_layout.addWidget(self.units_label)
        form_layout.addRow("Расход топлива:", consumption_layout)

        # 3. Поле для ввода коэффициента окисления
        self.oxidation_factor_input = QLineEdit()
        self.oxidation_factor_input.setValidator(QDoubleValidator(0.0, 1.0, 4, self))
        self.oxidation_factor_input.setText("1.0") # Значение по умолчанию
        self.oxidation_factor_input.setToolTip(
            "Доля окисленного углерода. Для газа и жидкости = 1.0. \n"
            "Для твердого топлива может быть иным. \n"
            "Для рядовых углей из таблицы 1.1 принимается равным 1."
        )
        form_layout.addRow("Коэффициент окисления (0-1):", self.oxidation_factor_input)

        main_layout.addLayout(form_layout)

        # --- Кнопка расчета и область результатов ---
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Метка для вывода результата
        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Устанавливаем первоначальные единицы измерения
        self._update_units()

    def _update_units(self):
        """
        Обновляет метку с единицами измерения в зависимости от выбранного топлива.
        Это делает интерфейс интуитивно понятным для пользователя.
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
            # 1. Сбор данных из полей ввода
            fuel_name = self.fuel_combobox.currentText()
            
            # Заменяем запятую на точку для корректного преобразования в float
            consumption_str = self.fuel_consumption_input.text().replace(',', '.')
            oxidation_str = self.oxidation_factor_input.text().replace(',', '.')

            # Проверка на пустые поля
            if not consumption_str or not oxidation_str:
                raise ValueError("Пожалуйста, заполните все поля.")

            fuel_consumption = float(consumption_str)
            oxidation_factor = float(oxidation_str)

            # 2. Вызов метода из модуля расчетов
            co2_emissions = self.calculator.calculate_co2_emissions(
                fuel_name=fuel_name,
                fuel_consumption=fuel_consumption,
                oxidation_factor=oxidation_factor
            )

            # 3. Отображение результата
            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            # Обработка ошибок ввода (например, пустые поля или некорректные числа)
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            # Обработка других непредвиденных ошибок
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")