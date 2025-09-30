# ui/category_23_tab.py - Виджет вкладки для расчетов по Категории 23.
# Реализует интерфейс для расчетов выбросов от сточных вод.
# Код написан полностью, без сокращений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QHBoxLayout, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from data_models import DataService
from calculations.category_23 import Category23Calculator

class Category23Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 23 "Очистка и сброс сточных вод".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category23Calculator(self.data_service)
        
        self.domestic_systems_rows = []

        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems([
            "Бытовые сточные воды",
            "Промышленные сточные воды"
        ])
        method_layout.addRow("Выберите тип сточных вод:", self.method_combobox)
        main_layout.addLayout(method_layout)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_domestic_widget())
        self.stacked_widget.addWidget(self._create_industrial_widget())
        main_layout.addWidget(self.stacked_widget)
        
        self.method_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
        self.calculate_button = QPushButton("Рассчитать выбросы CH4")
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
        
    def _create_scrollable_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(widget)
        return scroll_area, layout

    def _create_domestic_widget(self):
        scroll_area, layout = self._create_scrollable_widget()

        # Расчет TOW
        tow_group = QGroupBox("Расчет общей массы органических веществ (TOW)")
        tow_layout = QFormLayout(tow_group)
        self.dom_population = self._create_line_edit("", (0, 1e9, 0))
        tow_layout.addRow("Численность населения (чел):", self.dom_population)
        self.dom_bod = self._create_line_edit("60", (0.0, 1e9, 6)) # 60 г/чел/день - стандартное значение
        tow_layout.addRow("Образование БПК на жителя (г/чел/сутки):", self.dom_bod)
        self.dom_ind_factor = self._create_line_edit("1.25", (0.0, 1e9, 6))
        tow_layout.addRow("Коэф. для пром. сбросов (I):", self.dom_ind_factor)
        layout.addWidget(tow_group)
        
        # Общие параметры
        common_group = QGroupBox("Общие параметры для расчета выбросов")
        common_layout = QFormLayout(common_group)
        self.dom_sludge_removed = self._create_line_edit("0.0", (0.0, 1e12, 6))
        common_layout.addRow("Удалено с отстоем (S, кг БПК/год):", self.dom_sludge_removed)
        self.dom_recovered_ch4 = self._create_line_edit("0.0", (0.0, 1e12, 6))
        common_layout.addRow("Рекуперировано метана (R, кг CH4/год):", self.dom_recovered_ch4)
        self.dom_bo = self._create_line_edit("0.6", (0.0, 1.0, 6)) # 0.6 кг CH4/кг БПК - стандарт
        common_layout.addRow("Макс. способность образования CH4 (Bo):", self.dom_bo)
        layout.addWidget(common_group)

        # Системы очистки
        systems_group = QGroupBox("Системы очистки и сброса")
        self.domestic_systems_layout = QVBoxLayout(systems_group)
        add_btn = QPushButton("Добавить систему")
        add_btn.clicked.connect(self._add_domestic_system_row)
        self.domestic_systems_layout.addWidget(add_btn)
        layout.addWidget(systems_group)

        return scroll_area

    def _add_domestic_system_row(self):
        row_widget = QWidget()
        layout = QFormLayout(row_widget)
        
        population_fraction = self._create_line_edit("", (0.0, 1.0, 4), "доля от 0 до 1")
        layout.addRow("Доля населения (U_i):", population_fraction)
        
        treatment_fraction = self._create_line_edit("", (0.0, 1.0, 4), "доля от 0 до 1")
        layout.addRow("Доля стоков в системе (T_ij):", treatment_fraction)
        
        mcf_factor = self._create_line_edit("", (0.0, 1.0, 4), "доля от 0 до 1")
        layout.addRow("Коэф. для метана (MCF_j):", mcf_factor)
        
        remove_button = QPushButton("Удалить")
        layout.addRow(remove_button)

        row_data = {
            'widget': row_widget, 
            'population_fraction': population_fraction,
            'treatment_fraction': treatment_fraction,
            'mcf_factor': mcf_factor
        }
        self.domestic_systems_rows.append(row_data)
        self.domestic_systems_layout.insertWidget(self.domestic_systems_layout.count() - 1, row_widget)
        remove_button.clicked.connect(lambda: self._remove_row(row_data, self.domestic_systems_layout, self.domestic_systems_rows))

    def _create_industrial_widget(self):
        scroll_area, layout = self._create_scrollable_widget()

        tow_group = QGroupBox("Расчет органически разлагаемого материала (TOW)")
        tow_layout = QFormLayout(tow_group)
        self.ind_production = self._create_line_edit("", (0.0, 1e9, 6))
        tow_layout.addRow("Объем производства (P, т/год):", self.ind_production)
        self.ind_wastewater = self._create_line_edit("", (0.0, 1e9, 6))
        tow_layout.addRow("Объем сточных вод на ед. продукции (W, м³/т):", self.ind_wastewater)
        self.ind_cod = self._create_line_edit("", (0.0, 1e9, 6))
        tow_layout.addRow("Содержание разлагаемых компонентов (COD, кг ХПК/м³):", self.ind_cod)
        layout.addWidget(tow_group)

        emission_group = QGroupBox("Параметры для расчета выбросов")
        emission_layout = QFormLayout(emission_group)
        self.ind_sludge_removed = self._create_line_edit("0.0", (0.0, 1e12, 6))
        emission_layout.addRow("Удалено с отстоем (S, кг ХПК/год):", self.ind_sludge_removed)
        self.ind_recovered_ch4 = self._create_line_edit("0.0", (0.0, 1e12, 6))
        emission_layout.addRow("Рекуперировано метана (R, кг CH4/год):", self.ind_recovered_ch4)
        self.ind_bo = self._create_line_edit("0.25", (0.0, 1.0, 6)) # 0.25 кг CH4/кг ХПК - стандарт
        emission_layout.addRow("Макс. способность образования CH4 (Bo):", self.ind_bo)
        self.ind_mcf = self._create_line_edit("", (0.0, 1.0, 4))
        emission_layout.addRow("Поправочный коэффициент для метана (MCF):", self.ind_mcf)
        layout.addWidget(emission_group)
        
        return scroll_area

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
            ch4_emissions_tons = 0.0

            if method_index == 0: # Бытовые
                population = self._get_float(self.dom_population, "Численность населения")
                bod = self._get_float(self.dom_bod, "Образование БПК")
                ind_factor = self._get_float(self.dom_ind_factor, "Коэф. для пром. сбросов")
                tow = self.calculator.calculate_tow_domestic_by_population(population, bod, ind_factor)
                
                sludge_removed = self._get_float(self.dom_sludge_removed, "Удалено с отстоем")
                recovered_ch4 = self._get_float(self.dom_recovered_ch4, "Рекуперировано метана")
                bo = self._get_float(self.dom_bo, "Макс. способность образования CH4")
                
                if not self.domestic_systems_rows: raise ValueError("Добавьте хотя бы одну систему очистки.")

                systems = []
                for i, row in enumerate(self.domestic_systems_rows):
                    mcf = self._get_float(row['mcf_factor'], f"MCF для системы {i+1}")
                    ef = self.calculator.calculate_emission_factor(bo, mcf)
                    systems.append({
                        'population_fraction': self._get_float(row['population_fraction'], f"Доля населения для системы {i+1}"),
                        'treatment_fraction': self._get_float(row['treatment_fraction'], f"Доля стоков для системы {i+1}"),
                        'emission_factor': ef
                    })
                ch4_emissions_tons = self.calculator.calculate_domestic_ch4_emissions(tow, sludge_removed, recovered_ch4, systems)

            elif method_index == 1: # Промышленные
                production = self._get_float(self.ind_production, "Объем производства")
                wastewater = self._get_float(self.ind_wastewater, "Объем сточных вод")
                cod = self._get_float(self.ind_cod, "Содержание разлагаемых компонентов")
                tow = self.calculator.calculate_tow_industrial(production, wastewater, cod)

                sludge_removed = self._get_float(self.ind_sludge_removed, "Удалено с отстоем")
                recovered_ch4 = self._get_float(self.ind_recovered_ch4, "Рекуперировано метана")
                bo = self._get_float(self.ind_bo, "Макс. способность образования CH4")
                mcf = self._get_float(self.ind_mcf, "Поправочный коэффициент")
                ef = self.calculator.calculate_emission_factor(bo, mcf)
                
                ch4_emissions_tons = self.calculator.calculate_industrial_ch4_emissions(tow, sludge_removed, ef, recovered_ch4)

            self.result_label.setText(f"Результат: {ch4_emissions_tons:.4f} тонн CH4")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")