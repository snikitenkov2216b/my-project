# ui/category_22_tab.py - Виджет вкладки для расчетов по Категории 22.
# Реализует интерфейс для расчетов выбросов при сжигании отходов.
# Код написан полностью, без сокращений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_22 import Category22Calculator

class Category22Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 22 "Сжигание отходов".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category22Calculator(self.data_service)
        
        self.multicomponent_rows = []

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Выбор типа расчета ---
        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "CO2 от твердых отходов (общий метод, Ф. 3)",
            "CO2 от многокомпонентных отходов (ТКО, Ф. 3.1)",
            "CO2 от ископаемых жидких отходов (Ф. 3.2)",
            "N2O от сжигания отходов (Ф. 3.3)"
        ])
        method_layout.addRow("Выберите тип расчета:", self.method_combobox)
        main_layout.addLayout(method_layout)
        
        # --- Стек виджетов ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_solid_waste_widget())
        self.stacked_widget.addWidget(self._create_multicomponent_widget())
        self.stacked_widget.addWidget(self._create_liquid_waste_widget())
        self.stacked_widget.addWidget(self._create_n2o_widget())
        main_layout.addWidget(self.stacked_widget)
        
        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_line_edit(self, default_text="", validator_params=None, placeholder=""):
        line_edit = QLineEdit(default_text)
        line_edit.setPlaceholderText(placeholder)
        if validator_params:
            validator = QDoubleValidator(*validator_params, self)
            validator.setLocale(self.c_locale)
            line_edit.setValidator(validator)
        return line_edit

    def _create_solid_waste_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.solid_waste_mass = self._create_line_edit("", (0.0, 1e9, 6))
        layout.addRow("Масса сожженных отходов (т/год):", self.solid_waste_mass)
        self.solid_dm_fraction = self._create_line_edit("", (0.0, 1.0, 4), "доля от 0 до 1")
        layout.addRow("Доля сухого вещества (dm):", self.solid_dm_fraction)
        self.solid_cf_fraction = self._create_line_edit("", (0.0, 1.0, 4), "доля от 0 до 1")
        layout.addRow("Доля углерода в сухом веществе (CF):", self.solid_cf_fraction)
        self.solid_fcf_fraction = self._create_line_edit("", (0.0, 1.0, 4), "доля от 0 до 1")
        layout.addRow("Доля ископаемого углерода (FCF):", self.solid_fcf_fraction)
        self.solid_of_fraction = self._create_line_edit("", (0.0, 1.0, 4), "доля от 0 до 1")
        layout.addRow("Коэффициент окисления (OF):", self.solid_of_fraction)
        return widget

    def _create_multicomponent_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form = QFormLayout()
        self.multi_total_mass = self._create_line_edit("", (0.0, 1e9, 6))
        form.addRow("Общая масса сожженных отходов (т/год):", self.multi_total_mass)
        self.multi_of_fraction = self._create_line_edit("", (0.0, 1.0, 4), "доля от 0 до 1")
        form.addRow("Коэффициент окисления (OF):", self.multi_of_fraction)
        layout.addLayout(form)

        group = QGroupBox("Морфологический состав отходов")
        self.multicomponent_layout = QVBoxLayout(group)
        add_btn = QPushButton("Добавить компонент")
        add_btn.clicked.connect(self._add_multicomponent_row)
        self.multicomponent_layout.addWidget(add_btn)
        layout.addWidget(group)

        scroll_area.setWidget(widget)
        return scroll_area

    def _add_multicomponent_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        combo = QComboBox()
        combo.addItems(self.data_service.get_waste_component_types_20_2())
        fraction_input = self._create_line_edit("", (0.0, 1.0, 4), "Доля компонента (0-1)")
        remove_button = QPushButton("Удалить")
        row_layout.addWidget(combo)
        row_layout.addWidget(fraction_input)
        row_layout.addWidget(remove_button)
        
        row_data = {'widget': row_widget, 'combo': combo, 'fraction': fraction_input}
        self.multicomponent_rows.append(row_data)
        self.multicomponent_layout.insertWidget(self.multicomponent_layout.count() - 1, row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data, self.multicomponent_layout, self.multicomponent_rows))

    def _remove_row(self, row_data, layout, storage):
        row_data['widget'].deleteLater()
        layout.removeWidget(row_data['widget'])
        storage.remove(row_data)

    def _create_liquid_waste_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.liquid_waste_mass = self._create_line_edit("", (0.0, 1e9, 6))
        layout.addRow("Масса сожженных жидких отходов (т/год):", self.liquid_waste_mass)
        self.liquid_carbon_fraction = self._create_line_edit("", (0.0, 1.0, 4), "доля от 0 до 1")
        layout.addRow("Доля углерода в жидких отходах (CLW):", self.liquid_carbon_fraction)
        self.liquid_of_fraction = self._create_line_edit("", (0.0, 1.0, 4), "доля от 0 до 1")
        layout.addRow("Коэффициент окисления (OF):", self.liquid_of_fraction)
        return widget

    def _create_n2o_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.n2o_waste_mass = self._create_line_edit("", (0.0, 1e9, 6))
        layout.addRow("Масса сожженных отходов (т/год, сырой вес):", self.n2o_waste_mass)
        self.n2o_ef_input = self._create_line_edit("", (0.0, 1e9, 6))
        layout.addRow("Коэффициент выбросов N2O (кг/т отходов):", self.n2o_ef_input)
        return widget

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(',', '.')
        if not text: raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        try:
            method_index = self.method_combobox.currentIndex()
            result_text = ""

            if method_index == 0: # CO2 от твердых отходов
                mass = self._get_float(self.solid_waste_mass, "Масса отходов")
                dm = self._get_float(self.solid_dm_fraction, "Доля сухого вещества")
                cf = self._get_float(self.solid_cf_fraction, "Доля углерода")
                fcf = self._get_float(self.solid_fcf_fraction, "Доля ископаемого углерода")
                of = self._get_float(self.solid_of_fraction, "Коэффициент окисления")
                co2_emissions = self.calculator.calculate_co2_emissions_solid_waste(mass, dm, cf, fcf, of)
                result_text = f"Результат: {co2_emissions:.4f} тонн CO2"

            elif method_index == 1: # CO2 от многокомпонентных отходов
                total_mass = self._get_float(self.multi_total_mass, "Общая масса отходов")
                of = self._get_float(self.multi_of_fraction, "Коэффициент окисления")
                if not self.multicomponent_rows: raise ValueError("Добавьте хотя бы один компонент отходов.")
                composition = [{'type': r['combo'].currentText(), 'fraction': self._get_float(r['fraction'], 'Доля компонента')} for r in self.multicomponent_rows]
                co2_emissions = self.calculator.calculate_co2_emissions_multicomponent(total_mass, composition, of)
                result_text = f"Результат: {co2_emissions:.4f} тонн CO2"

            elif method_index == 2: # CO2 от жидких отходов
                mass = self._get_float(self.liquid_waste_mass, "Масса жидких отходов")
                carbon_fraction = self._get_float(self.liquid_carbon_fraction, "Доля углерода")
                of = self._get_float(self.liquid_of_fraction, "Коэффициент окисления")
                co2_emissions = self.calculator.calculate_co2_emissions_liquid_waste(mass, carbon_fraction, of)
                result_text = f"Результат: {co2_emissions:.4f} тонн CO2"

            elif method_index == 3: # N2O от сжигания
                mass = self._get_float(self.n2o_waste_mass, "Масса отходов")
                ef = self._get_float(self.n2o_ef_input, "Коэффициент выбросов N2O")
                n2o_emissions = self.calculator.calculate_n2o_emissions_from_incineration(mass, ef)
                result_text = f"Результат: {n2o_emissions:.4f} тонн N2O"

            self.result_label.setText(result_text)

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")