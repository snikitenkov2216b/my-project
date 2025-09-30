# ui/category_19_tab.py - Виджет вкладки для расчетов по Категории 19.
# Реализует интерфейс для расчетов в дорожном хозяйстве.
# Код написан полностью, без сокращений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox, QScrollArea, QSpinBox
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

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

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Расчет по расходу энергоресурсов (Формула 19.1)",
            "Расчет по протяженности дорог (Формулы 19.2, 19.3)"
        ])
        method_layout.addRow("Выберите метод расчета:", self.method_combobox)
        main_layout.addLayout(method_layout)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_energy_consumption_widget())
        self.stacked_widget.addWidget(self._create_road_length_widget())
        main_layout.addWidget(self.stacked_widget)
        
        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_scrollable_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(widget)
        return scroll_area, layout

    def _create_energy_consumption_widget(self):
        scroll_area, layout = self._create_scrollable_widget()
        group = QGroupBox("Расход энергоресурсов")
        self.fuels_layout = QVBoxLayout(group)
        add_btn = QPushButton("Добавить энергоресурс")
        add_btn.clicked.connect(self._add_fuel_row)
        self.fuels_layout.addWidget(add_btn)
        layout.addWidget(group)
        return scroll_area

    def _create_road_length_widget(self):
        scroll_area, layout = self._create_scrollable_widget()
        group = QGroupBox("Дорожные работы")
        self.road_works_layout = QVBoxLayout(group)
        add_btn = QPushButton("Добавить вид работ")
        add_btn.clicked.connect(self._add_road_work_row)
        self.road_works_layout.addWidget(add_btn)
        layout.addWidget(group)
        return scroll_area

    def _add_fuel_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        
        combo = QComboBox()
        # Используем топливо из общих таблиц
        items = self.data_service.get_fuels_table_1_1()
        combo.addItems(items)
        
        consumption = QLineEdit(placeholderText="Расход, т")
        # ИСПРАВЛЕНО
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        consumption.setValidator(validator)

        remove_button = QPushButton("Удалить")
        
        row_layout.addWidget(combo)
        row_layout.addWidget(consumption)
        row_layout.addWidget(remove_button)
        
        row_data = {'widget': row_widget, 'combo': combo, 'consumption': consumption}
        self.fuel_rows.append(row_data)
        self.fuels_layout.insertWidget(self.fuels_layout.count() - 1, row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data, self.fuels_layout, self.fuel_rows))

    def _add_road_work_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)

        type_combo = QComboBox()
        type_combo.addItems(self.data_service.get_road_types_table_19_1())
        
        stage_combo = QComboBox()
        stage_combo.addItems(self.data_service.get_road_stages_table_19_1())

        category_combo = QComboBox()
        category_combo.addItems(list(self.data_service.table_19_1["Автомобильные дороги федерального значения"]["Содержание"].keys()))

        length_input = QLineEdit(placeholderText="Протяженность, км")
        # ИСПРАВЛЕНО
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        length_input.setValidator(validator)
        
        years_input = QSpinBox()
        years_input.setRange(1, 100)
        years_input.setSuffix(" лет")
        
        remove_button = QPushButton("Удалить")

        row_layout.addWidget(type_combo)
        row_layout.addWidget(stage_combo)
        row_layout.addWidget(category_combo)
        row_layout.addWidget(length_input)
        row_layout.addWidget(years_input)
        row_layout.addWidget(remove_button)

        row_data = {'widget': row_widget, 'type': type_combo, 'stage': stage_combo, 
                    'category': category_combo, 'length': length_input, 'years': years_input}
        self.road_work_rows.append(row_data)
        self.road_works_layout.insertWidget(self.road_works_layout.count() - 1, row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data, self.road_works_layout, self.road_work_rows))

    def _remove_row(self, row_data, layout, storage):
        row_data['widget'].deleteLater()
        layout.removeWidget(row_data['widget'])
        storage.remove(row_data)

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(',', '.')
        if not text: raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        try:
            method_index = self.method_combobox.currentIndex()
            co2_emissions = 0.0

            if method_index == 0: # По расходу энергоресурсов
                if not self.fuel_rows:
                    raise ValueError("Добавьте хотя бы один энергоресурс.")
                
                fuel_data = []
                for i, row in enumerate(self.fuel_rows):
                    name = row['combo'].currentText()
                    consumption = self._get_float(row['consumption'], f"Расход для '{name}' (строка {i+1})")
                    fuel_data.append({'name': name, 'consumption': consumption})
                
                co2_emissions = self.calculator.calculate_from_energy_consumption(fuel_data)
                self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")

            elif method_index == 1: # По протяженности дорог
                if not self.road_work_rows:
                    raise ValueError("Добавьте хотя бы один вид дорожных работ.")
                    
                road_works_data = []
                for i, row in enumerate(self.road_work_rows):
                    length = self._get_float(row['length'], f"Протяженность (строка {i+1})")
                    road_works_data.append({
                        'type': row['type'].currentText(),
                        'stage': row['stage'].currentText(),
                        'category': row['category'].currentText(),
                        'length': length,
                        'years': row['years'].value()
                    })
                
                co2_emissions_per_year = self.calculator.calculate_from_road_length(road_works_data)
                self.result_label.setText(f"Результат: {co2_emissions_per_year:.4f} тонн CO2 в год")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")