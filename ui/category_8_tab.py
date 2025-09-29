# ui/category_8_tab.py - Виджет вкладки для расчетов по Категории 8.
# Реализует динамический интерфейс для ввода данных по производству стекла.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QHBoxLayout, QGroupBox
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_8 import Category8Calculator

class Category8Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 8 "Производство стекла".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category8Calculator(self.data_service)
        self.carbonate_rows = []
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        group_box = QGroupBox("Карбонатное сырье, используемое в шихте")
        self.carbonates_layout = QVBoxLayout()
        group_box.setLayout(self.carbonates_layout)
        
        add_button = QPushButton("Добавить карбонат")
        add_button.clicked.connect(self._add_carbonate_row)

        main_layout.addWidget(group_box)
        main_layout.addWidget(add_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _add_carbonate_row(self):
        """Добавляет новую динамическую строку для ввода данных по карбонату."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        
        combo = QComboBox()
        # Стекольное производство использует карбонаты из обеих таблиц 6.1 и 8.1
        carbonates_6_1 = self.data_service.get_carbonate_formulas_table_6_1()
        carbonates_8_1 = self.data_service.get_glass_carbonate_formulas_table_8_1()
        all_carbonates = sorted(list(set(carbonates_6_1 + carbonates_8_1)))
        combo.addItems(all_carbonates)
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("Масса, т")
        
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        line_edit.setValidator(validator)
        
        remove_button = QPushButton("Удалить")
        
        row_layout.addWidget(QLabel("Карбонат:"))
        row_layout.addWidget(combo)
        row_layout.addWidget(line_edit)
        row_layout.addWidget(remove_button)
        
        row_data = {'widget': row_widget, 'combo': combo, 'input': line_edit}
        self.carbonate_rows.append(row_data)
        self.carbonates_layout.addWidget(row_widget)
        
        remove_button.clicked.connect(lambda: self._remove_row(row_data, self.carbonates_layout, self.carbonate_rows))

    def _remove_row(self, row_data, target_layout, storage_list):
        """Удаляет строку из интерфейса и из списка хранения."""
        row_widget = row_data['widget']
        target_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        storage_list.remove(row_data)

    def _perform_calculation(self):
        """Выполняет расчет на основе введенных данных."""
        try:
            if not self.carbonate_rows:
                raise ValueError("Добавьте хотя бы один вид карбонатного сырья.")
            
            carbonates_data = []
            for row in self.carbonate_rows:
                name = row['combo'].currentText()
                mass_str = row['input'].text().replace(',', '.')
                if not mass_str:
                    raise ValueError(f"Не заполнено поле массы для '{name}'.")
                # Передаем данные в калькулятор. Степень кальцинирования по умолчанию 1.0
                carbonates_data.append({
                    'name': name, 
                    'mass': float(mass_str),
                    'calcination_degree': 1.0 
                })
            
            co2_emissions = self.calculator.calculate_emissions(carbonates_data)

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")