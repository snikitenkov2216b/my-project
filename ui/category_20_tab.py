# ui/category_20_tab.py - Виджет вкладки для расчетов по Категории 20.
# Реализует интерфейс для захоронения и биологической переработки отходов.
# Код написан полностью, без сокращений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox, QScrollArea, QTextEdit
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_20 import Category20Calculator

class Category20Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 20 "Захоронение и биологическая переработка твердых отходов".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category20Calculator(self.data_service)
        
        self.landfill_historical_rows = []

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Захоронение твердых отходов (Метод ЗПП)",
            "Биологическая переработка отходов"
        ])
        method_layout.addRow("Выберите тип процесса:", self.method_combobox)
        main_layout.addLayout(method_layout)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_landfill_widget())
        self.stacked_widget.addWidget(self._create_biological_treatment_widget())
        main_layout.addWidget(self.stacked_widget)
        
        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QTextEdit()
        self.result_label.setReadOnly(True)
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.result_label.setText("Результат:...")
        main_layout.addWidget(self.result_label)

    def _create_scrollable_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(widget)
        return scroll_area, layout

    def _create_landfill_widget(self):
        scroll_area, layout = self._create_scrollable_widget()

        params_group = QGroupBox("Параметры модели затухания первого порядка (ЗПП)")
        params_layout = QFormLayout(params_group)

        self.landfill_doc_input = self._create_line_edit((0.0, 1.0, 6), "0.15")
        params_layout.addRow("Доля разлагаемого углерода (DOC, доля):", self.landfill_doc_input)
        self.landfill_docf_input = self._create_line_edit((0.0, 1.0, 6), "0.5")
        params_layout.addRow("Доля DOC, способного к разложению (DOCf, доля):", self.landfill_docf_input)
        self.landfill_mcf_input = self._create_line_edit((0.0, 1.0, 6), "1.0")
        params_layout.addRow("Поправочный коэффициент для метана (MCF, доля):", self.landfill_mcf_input)
        self.landfill_f_input = self._create_line_edit((0.0, 1.0, 6), "0.5")
        params_layout.addRow("Доля CH4 в свалочном газе (F, доля):", self.landfill_f_input)
        self.landfill_k_input = self._create_line_edit((0.0, 1.0, 6), "0.05")
        params_layout.addRow("Постоянная реакции разложения (k, 1/год):", self.landfill_k_input)
        self.landfill_r_input = self._create_line_edit((0.0, 1e9, 6), "0.0")
        params_layout.addRow("Рекуперированный CH4 (R, Гг/год):", self.landfill_r_input)
        self.landfill_ox_input = self._create_line_edit((0.0, 1.0, 6), "0.0")
        params_layout.addRow("Коэффициент окисления (OX, доля):", self.landfill_ox_input)
        layout.addWidget(params_group)

        history_group = QGroupBox("Данные о захоронении отходов (в хронологическом порядке)")
        self.landfill_history_layout = QVBoxLayout(history_group)
        add_btn = QPushButton("Добавить год")
        add_btn.clicked.connect(self._add_landfill_history_row)
        self.landfill_history_layout.addWidget(add_btn)
        layout.addWidget(history_group)

        return scroll_area

    def _create_biological_treatment_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.bio_treatment_type_combobox = QComboBox()
        self.bio_treatment_type_combobox.addItems(self.data_service.get_biological_treatment_types_table_21_1())
        layout.addRow("Тип переработки:", self.bio_treatment_type_combobox)

        self.bio_waste_mass_input = self._create_line_edit((0.0, 1e9, 6))
        layout.addRow("Масса отходов (тонн, сырой вес):", self.bio_waste_mass_input)

        return widget

    def _add_landfill_history_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        
        year_label = QLabel(f"Год {len(self.landfill_historical_rows) + 1}:")
        mass_input = QLineEdit()
        mass_input.setPlaceholderText("Масса отходов, Гг")
        # ИСПРАВЛЕНО
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        mass_input.setValidator(validator)
        
        remove_button = QPushButton("Удалить")
        
        row_layout.addWidget(year_label)
        row_layout.addWidget(mass_input)
        row_layout.addWidget(remove_button)
        
        row_data = {'widget': row_widget, 'mass_input': mass_input}
        self.landfill_historical_rows.append(row_data)
        self.landfill_history_layout.insertWidget(self.landfill_history_layout.count() - 1, row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data, self.landfill_history_layout, self.landfill_historical_rows))

    def _remove_row(self, row_data, layout, storage):
        row_widget = row_data['widget']
        layout.removeWidget(row_widget)
        row_widget.deleteLater()
        storage.remove(row_data)
        # Обновляем нумерацию годов
        if storage is self.landfill_historical_rows:
            for i, row in enumerate(storage):
                row['widget'].findChild(QLabel).setText(f"Год {i+1}:")

    def _create_line_edit(self, validator_params, default_text=""):
        line_edit = QLineEdit(default_text)
        validator = QDoubleValidator(*validator_params, self)
        validator.setLocale(self.c_locale)
        line_edit.setValidator(validator)
        return line_edit

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(',', '.')
        if not text: raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        try:
            method_index = self.method_combobox.currentIndex()
            
            if method_index == 0: # Захоронение ТКО
                if not self.landfill_historical_rows:
                    raise ValueError("Добавьте данные о захоронении хотя бы за один год.")

                doc = self._get_float(self.landfill_doc_input, "DOC")
                doc_f = self._get_float(self.landfill_docf_input, "DOCf")
                mcf = self._get_float(self.landfill_mcf_input, "MCF")
                f = self._get_float(self.landfill_f_input, "F")
                k = self._get_float(self.landfill_k_input, "k")
                R = self._get_float(self.landfill_r_input, "R")
                OX = self._get_float(self.landfill_ox_input, "OX")
                
                historical_waste = []
                for i, row in enumerate(self.landfill_historical_rows):
                    mass = self._get_float(row['mass_input'], f"Масса отходов за Год {i+1}")
                    historical_waste.append(mass)

                emissions_list = self.calculator.calculate_landfill_ch4_emissions(
                    historical_waste, doc, doc_f, mcf, f, k, R, OX
                )
                
                result_text = "Результат (выбросы CH4 в тоннах):\n"
                for year, emission in enumerate(emissions_list, 1):
                    result_text += f"Год {year}: {emission:.4f}\n"
                self.result_label.setText(result_text)

            elif method_index == 1: # Биологическая переработка
                waste_mass = self._get_float(self.bio_waste_mass_input, "Масса отходов")
                treatment_type = self.bio_treatment_type_combobox.currentText()
                
                emissions = self.calculator.calculate_biological_treatment_emissions(waste_mass, treatment_type)
                
                result_text = (
                    f"Результат:\n"
                    f"Выбросы CH4: {emissions['ch4']:.4f} тонн\n"
                    f"Выбросы N2O: {emissions['n2o']:.4f} тонн"
                )
                self.result_label.setText(result_text)

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText(f"Результат: Ошибка - {e}")