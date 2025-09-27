# ui/category_19_tab.py - Виджет вкладки для расчетов по Категории 19.
# Реализует интерфейс для дорожного хозяйства.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QGroupBox, QHBoxLayout
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt

from data_models import DataService
from calculations.category_19 import Category19Calculator

class Category19Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 19 "Дорожное хозяйство".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category19Calculator(self.data_service)
        
        self.fuel_rows = []
        self.road_work_rows = []

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Выбор метода расчета ---
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Расчет по расходу энергоресурсов",
            "Расчет по протяженности дорог"
        ])
        main_layout.addWidget(QLabel("Выберите метод расчета:"))
        main_layout.addWidget(self.method_combobox)

        # --- Стек виджетов для разных методов ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_energy_consumption_widget())
        self.stacked_widget.addWidget(self._create_road_length_widget())
        main_layout.addWidget(self.stacked_widget)

        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)

        # --- Кнопка расчета и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_energy_consumption_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Энергоресурсы")
        self.fuels_layout = QVBoxLayout()
        add_button = QPushButton("Добавить топливо")
        add_button.clicked.connect(self._add_fuel_row)
        group.setLayout(self.fuels_layout)
        layout.addWidget(group)
        layout.addWidget(add_button)
        return widget

    def _create_road_length_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Участки дорожных работ")
        self.road_works_layout = QVBoxLayout()
        add_button = QPushButton("Добавить участок работ")
        add_button.clicked.connect(self._add_road_work_row)
        group.setLayout(self.road_works_layout)
        layout.addWidget(group)
        layout.addWidget(add_button)
        return widget

    def _add_fuel_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        
        combo = QComboBox(self)
        fuels = [f['fuel'] for f in self.data_service.table_18_1]
        combo.addItems(fuels)
        
        consumption_input = QLineEdit(placeholderText="Расход, т")
        consumption_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        
        remove_button = QPushButton("Удалить")
        
        row_layout.addWidget(combo)
        row_layout.addWidget(consumption_input)
        row_layout.addWidget(remove_button)
        
        row_data = {'widget': row_widget, 'combo': combo, 'input': consumption_input}
        self.fuel_rows.append(row_data)
        self.fuels_layout.addWidget(row_widget)
        
        remove_button.clicked.connect(lambda: self._remove_row(row_data, self.fuels_layout, self.fuel_rows))

    def _add_road_work_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        
        type_combo = QComboBox(self)
        type_combo.addItems(self.data_service.get_road_types_table_19_1())
        
        category_combo = QComboBox(self)
        category_combo.addItems(["I", "II", "III", "IV", "V"])
        
        stage_combo = QComboBox(self)
        stage_combo.addItems(self.data_service.get_road_stages_table_19_1())

        length_input = QLineEdit(placeholderText="Протяженность, км")
        length_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        
        years_input = QLineEdit(placeholderText="Срок, лет")
        years_input.setValidator(QDoubleValidator(1.0, 100.0, 1, self))
        
        remove_button = QPushButton("Удалить")

        row_layout.addWidget(type_combo)
        row_layout.addWidget(category_combo)
        row_layout.addWidget(stage_combo)
        row_layout.addWidget(length_input)
        row_layout.addWidget(years_input)
        row_layout.addWidget(remove_button)

        row_data = {
            'widget': row_widget, 'type': type_combo, 'category': category_combo,
            'stage': stage_combo, 'length': length_input, 'years': years_input
        }
        self.road_work_rows.append(row_data)
        self.road_works_layout.addWidget(row_widget)
        
        remove_button.clicked.connect(lambda: self._remove_row(row_data, self.road_works_layout, self.road_work_rows))

    def _remove_row(self, row_data, layout, storage):
        row_data['widget'].deleteLater()
        layout.removeWidget(row_data['widget'])
        storage.remove(row_data)

    def _perform_calculation(self):
        try:
            current_index = self.method_combobox.currentIndex()
            co2_emissions = 0.0

            if current_index == 0: # По расходу
                fuels = [{'name': r['combo'].currentText(), 'consumption': float(r['input'].text().replace(',', '.'))} for r in self.fuel_rows if r['input'].text()]
                if not fuels: raise ValueError("Добавьте хотя бы один вид топлива.")
                co2_emissions = self.calculator.calculate_from_energy_consumption(fuels)

            elif current_index == 1: # По протяженности
                works = []
                for r in self.road_work_rows:
                    if r['length'].text() and r['years'].text():
                        works.append({
                            'type': r['type'].currentText(),
                            'category': r['category'].currentText(),
                            'stage': r['stage'].currentText(),
                            'length': float(r['length'].text().replace(',', '.')),
                            'years': int(r['years'].text().replace(',', '.'))
                        })
                if not works: raise ValueError("Добавьте хотя бы один участок работ.")
                co2_emissions = self.calculator.calculate_from_road_length(works)
            
            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2/год")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")