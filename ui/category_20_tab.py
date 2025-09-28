# ui/category_20_tab.py - Виджет вкладки для расчетов по Категории 20.
# Реализует интерфейс для захоронения и биологической переработки отходов.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QTextEdit
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt, QLocale # <--- ДОБАВЛЕН ИМПОРТ QLocale

from data_models import DataService
from calculations.category_20 import Category20Calculator

class Category20Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 20 "Захоронение твердых отходов".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category20Calculator(self.data_service)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Создаем локаль один раз для всего класса
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

        # --- Выбор типа расчета ---
        self.calc_type_combobox = QComboBox()
        self.calc_type_combobox.addItems([
            "Захоронение отходов (расчет CH4)",
            "Биологическая переработка (расчет CH4 и N2O)"
        ])
        main_layout.addWidget(QLabel("Выберите тип процесса:"))
        main_layout.addWidget(self.calc_type_combobox)

        # --- Стек виджетов ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_landfill_widget())
        self.stacked_widget.addWidget(self._create_biological_treatment_widget())
        main_layout.addWidget(self.stacked_widget)

        self.calc_type_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)

        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setPlaceholderText("Результаты появятся здесь...")
        main_layout.addWidget(self.result_display)

    def _create_landfill_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.waste_mass_input = QLineEdit("100")
        waste_mass_validator = QDoubleValidator(0.0, 1e9, 6, self)
        waste_mass_validator.setLocale(self.c_locale)
        self.waste_mass_input.setValidator(waste_mass_validator)
        layout.addRow("Ежегодная масса отходов (Гг/год):", self.waste_mass_input)

        self.doc_input = QLineEdit("0.15")
        doc_validator = QDoubleValidator(0.0, 1.0, 4, self)
        doc_validator.setLocale(self.c_locale)
        self.doc_input.setValidator(doc_validator)
        layout.addRow("Доля DOC в отходах (доля):", self.doc_input)
        
        self.doc_f_input = QLineEdit("0.5")
        doc_f_validator = QDoubleValidator(0.0, 1.0, 4, self)
        doc_f_validator.setLocale(self.c_locale)
        self.doc_f_input.setValidator(doc_f_validator)
        layout.addRow("Доля разлагаемого DOC (DOCf, доля):", self.doc_f_input)

        self.mcf_combobox = QComboBox()
        self.mcf_combobox.addItems([f"{item['type']} ({item['MCF']})" for item in self.data_service.table_20_5])
        layout.addRow("Тип объекта (MCF):", self.mcf_combobox)

        self.f_input = QLineEdit("0.5")
        f_validator = QDoubleValidator(0.0, 1.0, 4, self)
        f_validator.setLocale(self.c_locale)
        self.f_input.setValidator(f_validator)
        layout.addRow("Доля CH4 в свалочном газе (F, доля):", self.f_input)
        
        self.k_input = QLineEdit("0.05")
        k_validator = QDoubleValidator(0.0, 1.0, 4, self)
        k_validator.setLocale(self.c_locale)
        self.k_input.setValidator(k_validator)
        layout.addRow("Постоянная реакции (k, 1/год):", self.k_input)
        
        self.years_input = QLineEdit("20")
        self.years_input.setValidator(QIntValidator(1, 100, self))
        layout.addRow("Период расчета (лет):", self.years_input)
        
        return widget

    def _create_biological_treatment_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.bio_treatment_type_combobox = QComboBox()
        self.bio_treatment_type_combobox.addItems(self.data_service.get_biological_treatment_types_table_21_1())
        layout.addRow("Тип переработки:", self.bio_treatment_type_combobox)
        
        self.bio_waste_mass_input = QLineEdit()
        bio_waste_validator = QDoubleValidator(0.0, 1e9, 6, self)
        bio_waste_validator.setLocale(self.c_locale)
        self.bio_waste_mass_input.setValidator(bio_waste_validator)
        layout.addRow("Масса отходов (тонн, сырой вес):", self.bio_waste_mass_input)

        return widget

    def _perform_calculation(self):
        try:
            current_index = self.calc_type_combobox.currentIndex()
            
            if current_index == 0: # Захоронение
                waste_mass = float(self.waste_mass_input.text().replace(',', '.'))
                doc = float(self.doc_input.text().replace(',', '.'))
                doc_f = float(self.doc_f_input.text().replace(',', '.'))
                mcf_text = self.mcf_combobox.currentText()
                mcf = float(mcf_text[mcf_text.rfind('(')+1:-1])
                f = float(self.f_input.text().replace(',', '.'))
                k = float(self.k_input.text().replace(',', '.'))
                years = int(self.years_input.text())

                emissions = self.calculator.calculate_landfill_ch4_emissions(waste_mass, doc, doc_f, mcf, f, k, years)
                
                result_text = "Ежегодные выбросы CH4 (тонн):\n"
                for i, val in enumerate(emissions, 1):
                    result_text += f"Год {i}: {val:.4f}\n"
                self.result_display.setText(result_text)

            elif current_index == 1: # Био-переработка
                waste_mass_str = self.bio_waste_mass_input.text().replace(',', '.')
                if not waste_mass_str: raise ValueError("Введите массу отходов.")
                waste_mass = float(waste_mass_str)
                treatment_type = self.bio_treatment_type_combobox.currentText()
                
                emissions = self.calculator.calculate_biological_treatment_emissions(waste_mass, treatment_type)
                
                result_text = (
                    f"Выбросы CH4: {emissions['ch4']:.4f} тонн\n"
                    f"Выбросы N2O: {emissions['n2o']:.4f} тонн"
                )
                self.result_display.setText(result_text)

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_display.setText(f"Критическая ошибка: {e}")