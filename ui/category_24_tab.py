# ui/category_24_tab.py - Виджет вкладки для расчетов по Категории 24.
# Код обновлен для приема калькулятора, добавления подсказок и логирования.
# Комментарии на русском. Поддержка UTF-8.

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QGroupBox, QTextEdit
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_24 import Category24Calculator
from ui.tab_data_mixin import TabDataMixin


class Category24Tab(TabDataMixin, QWidget):
    """
    Класс виджета-вкладки для Категории 24 "Выбросы закиси азота из сточных вод".
    """
    def __init__(self, calculator: Category24Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self); main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        nitrogen_group = QGroupBox("Расчет общего количества азота в сточных водах (Формула 4.8)"); nitrogen_layout = QFormLayout(nitrogen_group)
        self.population_input = self._create_line_edit((0, 1e9, 0)); nitrogen_layout.addRow("Численность населения (P, чел):", self.population_input)
        self.protein_input = self._create_line_edit((0.0, 1000.0, 4), "30.0", "Среднегодовое потребление белка. Стандарт: 30 кг/чел/год.")
        nitrogen_layout.addRow("Потребление протеина (кг/чел/год):", self.protein_input)
        self.fnpr_input = self._create_line_edit((0.0, 1.0, 4), "0.16", "Доля азота в белке. Стандарт: 0.16 кг N/кг белка.")
        nitrogen_layout.addRow("Доля азота в протеине (F_NPR):", self.fnpr_input)
        self.fnon_con_input = self._create_line_edit((0.0, 10.0, 4), "1.1", "Коэф., учитывающий белок в непотребляемых продуктах. Стандарт: 1.1.")
        nitrogen_layout.addRow("Коэф. непотребленного протеина (F_NON-CON):", self.fnon_con_input)
        self.find_com_input = self._create_line_edit((0.0, 10.0, 4), "1.25", "Коэф., учитывающий пром. и коммерческий сброс белка. Стандарт: 1.25.")
        nitrogen_layout.addRow("Коэф. пром. протеина (F_IND-COM):", self.find_com_input)
        self.sludge_nitrogen_input = self._create_line_edit((0.0, 1e12, 6), "0.0", "Общее количество азота, удаленное с осадком сточных вод за год.")
        nitrogen_layout.addRow("Азот, удаленный с отстоем (N_ОТСТОЙ, кг N/год):", self.sludge_nitrogen_input)
        main_layout.addWidget(nitrogen_group)

        emission_group = QGroupBox("Расчет выбросов N2O (Формула 4.7)"); emission_layout = QFormLayout(emission_group)
        self.emission_factor_input = self._create_line_edit((0.0, 1.0, 6), "0.005", "Коэффициент выбросов для N2O из сточных вод. Стандарт: 0.005 кг N2O-N/кг N.")
        emission_layout.addRow("Коэффициент выбросов (EF_сток, кг N2O-N/кг N):", self.emission_factor_input)
        main_layout.addWidget(emission_group)

        self.calculate_button = QPushButton("Рассчитать выбросы N2O"); self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.result_label = QTextEdit(); self.result_label.setReadOnly(True); self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.result_label.setText("Результат:..."); main_layout.addWidget(self.result_label)

    def _create_line_edit(self, validator_params, default_text="", tooltip=""):
        line_edit = QLineEdit(default_text); line_edit.setToolTip(tooltip)
        validator = QDoubleValidator(*validator_params, self); validator.setLocale(self.c_locale); line_edit.setValidator(validator)
        return line_edit

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(',', '.');
        if not text: raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        try:
            population = self._get_float(self.population_input, "Численность населения"); protein = self._get_float(self.protein_input, "Потребление протеина")
            fnpr = self._get_float(self.fnpr_input, "Доля азота"); fnon_con = self._get_float(self.fnon_con_input, "Коэф. непотребленного протеина")
            find_com = self._get_float(self.find_com_input, "Коэф. пром. протеина"); sludge_nitrogen = self._get_float(self.sludge_nitrogen_input, "Азот в отстое")
            
            nitrogen_in_effluent = self.calculator.calculate_nitrogen_in_effluent(int(population), protein, fnpr, fnon_con, find_com, sludge_nitrogen)
            emission_factor = self._get_float(self.emission_factor_input, "Коэффициент выбросов")
            n2o_emissions = self.calculator.calculate_n2o_emissions_from_effluent(nitrogen_in_effluent, emission_factor)

            result_text = (f"Результат:\nОбщее кол-во азота в стоках (N_сток): {nitrogen_in_effluent:.2f} кг N/год\n"
                           f"Выбросы N2O: {n2o_emissions:.4f} тонн/год")
            self.result_label.setText(result_text)
            logging.info(f"Category 24 calculation successful: N_effluent={nitrogen_in_effluent}, N2O={n2o_emissions}")
        except ValueError as e:
            logging.error(f"Category 24 Calculation - ValueError: {e}"); QMessageBox.warning(self, "Ошибка ввода", str(e)); self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(f"Category 24 Calculation - Unexpected error: {e}", exc_info=True); QMessageBox.critical(self, "Критическая ошибка", str(e)); self.result_label.setText("Результат: Ошибка")