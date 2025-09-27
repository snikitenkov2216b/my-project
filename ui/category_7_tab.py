# ui/category_7_tab.py - Виджет вкладки для расчетов по Категории 7.
# Реализует динамический интерфейс для двух методов расчета выбросов при производстве извести.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt

from data_models import DataService
from calculations.category_7 import Category7Calculator

class Category7Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 7 "Производство извести".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category7Calculator(self.data_service)
        self.carbonate_rows = # Хранилище для динамических строк сырья
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Выбор метода расчета ---
        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Расчет на основе расхода сырья",
            "Расчет на основе производства извести"
        ])
        method_layout.addRow("Выберите метод расчета:", self.method_combobox)
        main_layout.addLayout(method_layout)

        # --- Стек виджетов для разных форм ввода ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_raw_materials_widget())
        self.stacked_widget.addWidget(self._create_lime_widget())
        main_layout.addWidget(self.stacked_widget)

        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)

        # --- Кнопка расчета и область результатов ---
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_raw_materials_widget(self):
        """Создает виджет для метода 'на основе расхода сырья'."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        group_box = QGroupBox("Карбонатное сырье")
        self.carbonates_layout = QVBoxLayout()
        group_box.setLayout(self.carbonates_layout)
        
        add_button = QPushButton("Добавить карбонат")
        add_button.clicked.connect(self._add_carbonate_row)

        layout.addWidget(group_box)
        layout.addWidget(add_button, alignment=Qt.AlignmentFlag.AlignLeft)
        
        return widget

    def _add_carbonate_row(self):
        """Добавляет новую динамическую строку для ввода данных по карбонату."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        
        combo = QComboBox()
        # Используем те же карбонаты, что и для цемента (Таблица 6.1)
        carbonate_names = self.data_service.get_carbonate_formulas_table_6_1()
        combo.addItems(carbonate_names)
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("Масса, т")
        line_edit.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        
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

    def _create_lime_widget(self):
        """Создает виджет для метода 'на основе производства извести'."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.lime_production_input = QLineEdit()
        self.lime_production_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        layout.addRow("Масса произведенной извести (т):", self.lime_production_input)

        self.lime_cao_fraction_input = QLineEdit()
        self.lime_cao_fraction_input.setValidator(QDoubleValidator(0.0, 1.0, 4, self))
        self.lime_cao_fraction_input.setPlaceholderText("Например, 0.95")
        layout.addRow("Массовая доля CaO в извести (доля):", self.lime_cao_fraction_input)

        self.lime_mgo_fraction_input = QLineEdit()
        self.lime_mgo_fraction_input.setValidator(QDoubleValidator(0.0, 1.0, 4, self))
        self.lime_mgo_fraction_input.setPlaceholderText("Например, 0.01")
        layout.addRow("Массовая доля MgO в извести (доля):", self.lime_mgo_fraction_input)
        
        return widget

    def _perform_calculation(self):
        """Выполняет расчет в зависимости от выбранного метода."""
        current_method_index = self.method_combobox.currentIndex()
        try:
            co2_emissions = 0.0
            if current_method_index == 0: # Расчет на основе сырья
                if not self.carbonate_rows:
                    raise ValueError("Добавьте хотя бы один вид карбонатного сырья.")
                
                carbonates_data =
                for row in self.carbonate_rows:
                    name = row['combo'].currentText()
                    mass_str = row['input'].text().replace(',', '.')
                    if not mass_str:
                        raise ValueError(f"Не заполнено поле массы для '{name}'.")
                    carbonates_data.append({'name': name, 'mass': float(mass_str)})
                
                co2_emissions = self.calculator.calculate_based_on_raw_materials(carbonates_data)

            elif current_method_index == 1: # Расчет на основе извести
                lime_prod_str = self.lime_production_input.text().replace(',', '.')
                cao_frac_str = self.lime_cao_fraction_input.text().replace(',', '.')
                mgo_frac_str = self.lime_mgo_fraction_input.text().replace(',', '.')

                if not all([lime_prod_str, cao_frac_str, mgo_frac_str]):
                    raise ValueError("Пожалуйста, заполните все поля.")

                lime_production = float(lime_prod_str)
                cao_fraction = float(cao_frac_str)
                mgo_fraction = float(mgo_frac_str)

                co2_emissions = self.calculator.calculate_based_on_lime(
                    lime_production, cao_fraction, mgo_fraction
                )

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")