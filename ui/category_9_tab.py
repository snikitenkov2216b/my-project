# ui/category_9_tab.py - Виджет вкладки для расчетов по Категории 9.
# Реализует динамический интерфейс для ввода данных по производству керамики.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QHBoxLayout, QGroupBox
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt

from data_models import DataService
from calculations.category_9 import Category9Calculator

class Category9Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 9 "Производство керамических изделий".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category9Calculator(self.data_service)
        self.raw_material_rows = # Хранилище для динамических строк сырья
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Форма для ввода данных ---
        group_box = QGroupBox("Минеральное сырье, содержащее карбонаты")
        self.materials_layout = QVBoxLayout()
        group_box.setLayout(self.materials_layout)
        
        add_button = QPushButton("Добавить сырье")
        add_button.clicked.connect(self._add_material_row)

        main_layout.addWidget(group_box)
        main_layout.addWidget(add_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Кнопка расчета и область результатов ---
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _add_material_row(self):
        """Добавляет новую динамическую строку для ввода данных по сырью."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        
        combo = QComboBox()
        carbonate_names = self.data_service.get_carbonate_formulas_table_6_1()
        combo.addItems(carbonate_names)
        
        mass_input = QLineEdit()
        mass_input.setPlaceholderText("Масса сырья, т")
        mass_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        
        fraction_input = QLineEdit()
        fraction_input.setPlaceholderText("Доля карбоната (0-1)")
        fraction_input.setValidator(QDoubleValidator(0.0, 1.0, 4, self))

        remove_button = QPushButton("Удалить")
        
        row_layout.addWidget(QLabel("Карбонат в сырье:"))
        row_layout.addWidget(combo)
        row_layout.addWidget(mass_input)
        row_layout.addWidget(fraction_input)
        row_layout.addWidget(remove_button)
        
        row_data = {
            'widget': row_widget,
            'combo': combo,
            'mass_input': mass_input,
            'fraction_input': fraction_input
        }
        self.raw_material_rows.append(row_data)
        self.materials_layout.addWidget(row_widget)
        
        remove_button.clicked.connect(lambda: self._remove_row(row_data, self.materials_layout, self.raw_material_rows))

    def _remove_row(self, row_data, target_layout, storage_list):
        """Удаляет строку из интерфейса и из списка хранения."""
        row_widget = row_data['widget']
        target_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        storage_list.remove(row_data)

    def _perform_calculation(self):
        """Выполняет расчет на основе введенных данных."""
        try:
            if not self.raw_material_rows:
                raise ValueError("Добавьте хотя бы один вид сырья.")
            
            materials_data =
            for row in self.raw_material_rows:
                name = row['combo'].currentText()
                mass_str = row['mass_input'].text().replace(',', '.')
                fraction_str = row['fraction_input'].text().replace(',', '.')

                if not mass_str or not fraction_str:
                    raise ValueError(f"Не все поля заполнены для сырья с карбонатом '{name}'.")
                
                materials_data.append({
                    'carbonate_name': name,
                    'material_mass': float(mass_str),
                    'carbonate_fraction': float(fraction_str)
                })
            
            co2_emissions = self.calculator.calculate_emissions(materials_data)

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")