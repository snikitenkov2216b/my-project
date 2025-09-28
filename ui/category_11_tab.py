# ui/category_11_tab.py - Виджет вкладки для расчетов по Категории 11.
# Реализует интерфейс для ввода данных по выбросам N2O.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale # <--- ДОБАВЛЕН ИМПОРТ QLocale

from data_models import DataService
from calculations.category_11 import Category11Calculator

class Category11Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 11 "Производство азотной кислоты,
    капролактама, глиоксаля и глиоксиловой кислоты".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category11Calculator(self.data_service)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Создаем локаль, которая использует точку как разделитель
        c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

        # 1. Выпадающий список для выбора производственного процесса
        self.process_combobox = QComboBox()
        processes = self.data_service.get_ammonia_processes_table_11_1()
        self.process_combobox.addItems(processes)
        form_layout.addRow("Производственный процесс:", self.process_combobox)

        # 2. Поле для ввода массы произведенной продукции
        production_layout = QHBoxLayout()
        self.production_input = QLineEdit()
        
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(c_locale)
        self.production_input.setValidator(validator)
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
        
        self.production_input.setPlaceholderText("Введите числовое значение")
        production_layout.addWidget(self.production_input)
        production_layout.addWidget(QLabel("(т)"))
        form_layout.addRow("Масса произведенной продукции:", production_layout)
        
        main_layout.addLayout(form_layout)

        self.calculate_button = QPushButton("Рассчитать выбросы N2O")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _perform_calculation(self):
        """Выполняет расчет на основе введенных данных."""
        try:
            process_name = self.process_combobox.currentText()
            
            production_str = self.production_input.text().replace(',', '.')
            if not production_str:
                raise ValueError("Поле 'Масса произведенной продукции' не может быть пустым.")
            
            production_mass = float(production_str)

            n2o_emissions = self.calculator.calculate_n2o_emissions(
                process_name, production_mass
            )

            self.result_label.setText(f"Результат: {n2o_emissions:.4f} тонн N2O")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")