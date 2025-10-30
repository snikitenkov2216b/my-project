# ui/land_conversion_tab.py
"""
Вкладка для расчетов поглощения при конверсии земель.
"""
import logging
import math
from typing import List, Dict, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QGroupBox,
    QComboBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QSpinBox, QDoubleSpinBox, QMessageBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.absorption_agricultural import LandConversionCalculator
from data_models_extended import DataService

from ui.tab_data_mixin import TabDataMixin
from ui.absorption_utils import create_line_edit, get_float, handle_error


class LandConversionTab(TabDataMixin, QWidget):
    """Вкладка для расчетов по конверсии земель и кормовым угодьям (Формулы 91-100)."""
    def __init__(self, calculator: LandConversionCalculator, data_service: DataService, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.data_service = data_service
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()
        logging.info("LandConversionTab initialized.")

    def _init_ui(self):
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget); main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(main_widget)
        outer_layout = QVBoxLayout(self); outer_layout.addWidget(scroll_area)

        # --- Изменение запасов C при конверсии (Ф. 91) ---
        group_f91 = QGroupBox("Изменение запасов C при конверсии в пахотные земли (Формула 91)")
        layout_f91 = QFormLayout(group_f91)
        # Упрощенный ввод для примера
        self.f91_c_after = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Суммарный запас C ПОСЛЕ конверсии (все пулы), т C")
        self.f91_c_before = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Суммарный запас C ДО конверсии (все пулы), т C")
        self.f91_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь конверсии, га")
        self.f91_period = create_line_edit(self, "20", (1, 100, 1), tooltip="Период конверсии, лет (стандартно 20)")
        layout_f91.addRow("C после (СУММА, т C):", self.f91_c_after) # Указываем, что это сумма
        layout_f91.addRow("C до (СУММА, т C):", self.f91_c_before)   # Указываем, что это сумма
        layout_f91.addRow("Площадь конверсии (ΔA, га):", self.f91_area)
        layout_f91.addRow("Период конверсии (D, лет):", self.f91_period)
        calc_f91_btn = QPushButton("Рассчитать ΔC конверсии (Ф. 91)"); calc_f91_btn.clicked.connect(self._calculate_f91)
        layout_f91.addRow(calc_f91_btn)
        self.f91_result = QLabel("—")
        self.f91_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f91_result.setWordWrap(True)
        layout_f91.addRow("Результат:", self.f91_result)
        main_layout.addWidget(group_f91)

        # --- Выбросы от осушения/пожаров на переведенных землях (Ф. 92-95) ---
        emissions_group = QGroupBox("Выбросы на переведенных землях (Формулы 92-95)")
        emissions_layout = QVBoxLayout(emissions_group)
        layout_92_94 = QFormLayout()
        self.f92_94_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь осушенных переведенных земель, га")
        layout_92_94.addRow("Площадь осушения (A, га):", self.f92_94_area)
        # Ф.92 CO2
        self.f92_ef = create_line_edit(self, "5.9", (0, 100, 4), tooltip="Коэф. выброса CO2, т C/га/год (как для пашни)")
        layout_92_94.addRow("EF CO2 (т C/га/год):", self.f92_ef)
        calc_f92_btn = QPushButton("Рассчитать CO2 от осушения (Ф. 92)"); calc_f92_btn.clicked.connect(self._calculate_f92)
        layout_92_94.addRow(calc_f92_btn)
        # Ф.93 N2O
        self.f93_ef = create_line_edit(self, "7.0", (0, 100, 4), tooltip="Коэф. выброса N2O, кг N-N2O/га/год (как для пашни)")
        layout_92_94.addRow("EF N2O (кг N-N2O/га/год):", self.f93_ef)
        self.f92_result = QLabel("—")
        self.f92_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f92_result.setWordWrap(True)
        layout_92_94.addRow("Результат Ф.92:", self.f92_result)
        calc_f93_btn = QPushButton("Рассчитать N2O от осушения (Ф. 93)"); calc_f93_btn.clicked.connect(self._calculate_f93)
        layout_92_94.addRow(calc_f93_btn)
        # Ф.94 CH4
        self.f94_frac_ditch = create_line_edit(self, "0.5", (0, 1, 3), tooltip="Доля канав (как для пашни)")
        self.f94_ef_land = create_line_edit(self, "0.0", (0, 1e6, 4), tooltip="EF земли, кг CH4/га/год (как для пашни)")
        self.f93_result = QLabel("—")
        self.f93_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f93_result.setWordWrap(True)
        layout_92_94.addRow("Результат Ф.93:", self.f93_result)
        self.f94_ef_ditch = create_line_edit(self, "1165", (0, 1e6, 4), tooltip="EF канав, кг CH4/га/год (как для пашни)")
        layout_92_94.addRow("Доля канав (Frac_ditch):", self.f94_frac_ditch)
        layout_92_94.addRow("EF_land CH4 (кг/га/год):", self.f94_ef_land)
        layout_92_94.addRow("EF_ditch CH4 (кг/га/год):", self.f94_ef_ditch)
        calc_f94_btn = QPushButton("Рассчитать CH4 от осушения (Ф. 94)"); calc_f94_btn.clicked.connect(self._calculate_f94)
        layout_92_94.addRow(calc_f94_btn)
        self.f94_result = QLabel("—")
        self.f94_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f94_result.setWordWrap(True)
        layout_92_94.addRow("Результат:", self.f94_result)
        emissions_layout.addLayout(layout_92_94)
        # Ф.95 Пожары
        layout_f95 = QFormLayout()
        self.f95_area = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Площадь пожара на переведенных землях, га")
        self.f95_fuel_mass = create_line_edit(self, validator_params=(0, 1000, 4), tooltip="Масса топлива, т/га")
        self.f95_comb_factor = create_line_edit(self, validator_params=(0.01, 1.0, 3), tooltip="Коэффициент сгорания (доля)")
        self.f95_gas_type = QComboBox(); self.f95_gas_type.addItems(["CO2", "CH4", "N2O"]) # Уточнить EF для этих земель
        layout_f95.addRow("Площадь пожара (A, га):", self.f95_area)
        layout_f95.addRow("Масса топлива (MB, т/га):", self.f95_fuel_mass)
        layout_f95.addRow("Коэф. сгорания (C_f, доля):", self.f95_comb_factor)
        layout_f95.addRow("Тип газа:", self.f95_gas_type)
        calc_f95_btn = QPushButton("Рассчитать выброс от пожара (Ф. 95)"); calc_f95_btn.clicked.connect(self._calculate_f95)
        layout_f95.addRow(calc_f95_btn)
        self.f95_result = QLabel("—")
        self.f95_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f95_result.setWordWrap(True)
        layout_f95.addRow("Результат:", self.f95_result)
        emissions_layout.addLayout(layout_f95)
        main_layout.addWidget(emissions_group)


        # --- Изменение C в почвах корм. угодий (Ф. 96-100) ---
        grass_group = QGroupBox("Изменение C в почвах кормовых угодий (Формулы 96-100)")
        grass_layout = QVBoxLayout(grass_group)
        layout_f96 = QFormLayout()
        self.f96_c_plant = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Поступление C от растений, т C/год (из Ф.97)")
        self.f96_c_manure = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Поступление C с навозом, т C/год (из Ф.98)")
        self.f96_c_resp = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери C от дыхания, т C/год")
        self.f96_c_erosion = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери C от эрозии, т C/год (из Ф.99)")
        self.f96_c_hay = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Вынос C с сеном, т C/год (из Ф.100)")
        self.f96_c_feed = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Вынос C на корм скоту, т C/год")
        self.f96_c_green = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Вынос C с зеленой массой, т C/год")
        layout_f96.addRow("C растения (т C/год):", self.f96_c_plant)
        layout_f96.addRow("C навоз (т C/год):", self.f96_c_manure)
        layout_f96.addRow("C дыхание (т C/год):", self.f96_c_resp)
        layout_f96.addRow("C эрозия (т C/год):", self.f96_c_erosion)
        layout_f96.addRow("C сено (т C/год):", self.f96_c_hay)
        layout_f96.addRow("C корм (т C/год):", self.f96_c_feed)
        layout_f96.addRow("C зел. масса (т C/год):", self.f96_c_green)
        calc_f96_btn = QPushButton("Рассчитать ΔC корм. угодий (Ф. 96)"); calc_f96_btn.clicked.connect(self._calculate_f96)
        layout_f96.addRow(calc_f96_btn)
        self.f96_result = QLabel("—")
        self.f96_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f96_result.setWordWrap(True)
        layout_f96.addRow("Результат:", self.f96_result)
        grass_layout.addLayout(layout_f96)

        # Ф. 97: Поступление C от растений
        layout_f97 = QFormLayout()
        self.f97_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь кормовых угодий, га")
        self.f97_c_acc = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Аккумуляция углерода, т C/га/год")
        layout_f97.addRow("Площадь (A, га):", self.f97_area)
        layout_f97.addRow("Аккумуляция C (C_акк, т C/га/год):", self.f97_c_acc)
        calc_f97_btn = QPushButton("Рассчитать C растения (Ф. 97) -> подставить в Ф.96"); calc_f97_btn.clicked.connect(self._calculate_f97)
        layout_f97.addRow(calc_f97_btn)
        self.f97_result = QLabel("—")
        self.f97_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f97_result.setWordWrap(True)
        layout_f97.addRow("Результат:", self.f97_result)
        grass_layout.addLayout(layout_f97)

        # Ф. 98: Поступление C с навозом - Упрощенный интерфейс
        layout_f98 = QFormLayout()
        self.f98_manure_c = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Общее поступление C с навозом, т C/год (рассчитайте отдельно или используйте детальный расчет)")
        layout_f98.addRow("C навоз (Cmanure, т C/год):", self.f98_manure_c)

        # Детальный интерфейс для ввода данных по животным (LivestockData)
        livestock_detail_layout = QVBoxLayout()
        livestock_label = QLabel('Для детального расчета используйте таблицу:')
        livestock_detail_layout.addWidget(livestock_label)

        self.livestock_table = QTableWidget()
        self.livestock_table.setColumnCount(4)
        self.livestock_table.setHorizontalHeaderLabels(['Тип животного', 'Поголовье', 'Коэф. экскреции C', 'Время на пастбище (%)'])
        self.livestock_table.setRowCount(1)
        self.livestock_table.horizontalHeader().setStretchLastSection(True)
        livestock_detail_layout.addWidget(self.livestock_table)

        livestock_btn_layout = QHBoxLayout()
        add_livestock_btn = QPushButton('➕ Добавить тип')
        add_livestock_btn.clicked.connect(lambda: self.livestock_table.setRowCount(self.livestock_table.rowCount() + 1))
        remove_livestock_btn = QPushButton('➖ Удалить')
        remove_livestock_btn.clicked.connect(lambda: self.livestock_table.setRowCount(max(1, self.livestock_table.rowCount() - 1)))
        calc_livestock_btn = QPushButton('Рассчитать C навоза (детально)')
        calc_livestock_btn.clicked.connect(self._calculate_livestock_manure)
        livestock_btn_layout.addWidget(add_livestock_btn)
        livestock_btn_layout.addWidget(remove_livestock_btn)
        livestock_btn_layout.addWidget(calc_livestock_btn)
        livestock_detail_layout.addLayout(livestock_btn_layout)
        layout_f98.addRow(livestock_detail_layout)
        self.f98_result = QLabel("—")
        self.f98_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f98_result.setWordWrap(True)
        layout_f98.addRow("Результат:", self.f98_result)
        grass_layout.addLayout(layout_f98)

        # Ф. 99: Потери от эрозии
        layout_f99 = QFormLayout()
        self.f99_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь пастбищ, га")
        self.f99_erosion_factor = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Коэффициент эрозии, т C/га/год")
        layout_f99.addRow("Площадь (A, га):", self.f99_area)
        layout_f99.addRow("Коэф. эрозии (EFerosion, т C/га/год):", self.f99_erosion_factor)
        calc_f99_btn = QPushButton("Рассчитать C эрозии (Ф. 99) -> подставить в Ф.96"); calc_f99_btn.clicked.connect(self._calculate_f99)
        layout_f99.addRow(calc_f99_btn)
        self.f99_result = QLabel("—")
        self.f99_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f99_result.setWordWrap(True)
        layout_f99.addRow("Результат:", self.f99_result)
        grass_layout.addLayout(layout_f99)

        # Ф. 100: Вынос C с сеном
        layout_f100 = QFormLayout()
        self.f100_hay_yield = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Годовая урожайность сена, т/год")
        layout_f100.addRow("Урожайность сена (Yhay, т/год):", self.f100_hay_yield)
        calc_f100_btn = QPushButton("Рассчитать вынос C (Ф. 100) -> подставить в Ф.96"); calc_f100_btn.clicked.connect(self._calculate_f100)
        layout_f100.addRow(calc_f100_btn)
        self.f100_result = QLabel("—")
        self.f100_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f100_result.setWordWrap(True)
        layout_f100.addRow("Результат:", self.f100_result)
        grass_layout.addLayout(layout_f100)

        main_layout.addWidget(grass_group)

    # --- Методы расчета для LandConversionTab ---
    def _calculate_f91(self):
        try:
            # Упрощенно: считаем, что введены суммы
            c_after_sum = get_float(self.f91_c_after, "C после (Ф.91)")
            c_before_sum = get_float(self.f91_c_before, "C до (Ф.91)")
            area = get_float(self.f91_area, "Площадь конверсии (Ф.91)")
            period = get_float(self.f91_period, "Период конверсии (Ф.91)")
            # Передаем списки из одного элемента
            delta_c = self.calculator.calculate_conversion_carbon_change([c_after_sum], [c_before_sum], area, period)
            co2_eq = delta_c * (-44/12)
            result = (f"ΔC конверсии (Ф. 91):\nΔC = {delta_c:.4f} т C/год\nЭквивалент CO2: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.f91_result.setText(result); logging.info(f"LandConversionTab: F91 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 91")

    def _calculate_f92(self):
        try:
            area = get_float(self.f92_94_area, "Площадь осушения (Ф.92)")
            ef = get_float(self.f92_ef, "EF CO2 (Ф.92)")
            emission = self.calculator.calculate_converted_land_co2(area, ef)
            self.f92_result.setText(f"Выбросы CO2 от осушения (Ф. 92): {emission:.4f} т CO2/год")
            logging.info(f"LandConversionTab(F92): Result={emission:.4f} t CO2/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 92")

    def _calculate_f93(self):
        try:
            area = get_float(self.f92_94_area, "Площадь осушения (Ф.93)")
            ef = get_float(self.f93_ef, "EF N2O (Ф.93)")
            emission = self.calculator.calculate_converted_land_n2o(area, ef)
            co2_eq = emission * 265
            self.f93_result.setText(f"Выбросы N2O от осушения (Ф. 93): {emission:.6f} т N2O/год\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"LandConversionTab(F93): Result={emission:.6f} t N2O/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 93")

    def _calculate_f94(self):
        try:
            area = get_float(self.f92_94_area, "Площадь осушения (Ф.94)")
            frac_ditch = get_float(self.f94_frac_ditch, "Доля канав (Ф.94)")
            ef_land = get_float(self.f94_ef_land, "EF_land CH4 (Ф.94)")
            ef_ditch = get_float(self.f94_ef_ditch, "EF_ditch CH4 (Ф.94)")
            emission_kg = self.calculator.calculate_converted_land_ch4(area, frac_ditch, ef_land, ef_ditch)
            emission_t = emission_kg / 1000.0
            co2_eq = emission_t * 28
            self.f94_result.setText(f"Выбросы CH4 от осушения (Ф. 94): {emission_t:.6f} т CH4/год ({emission_kg:.3f} кг/год)\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"LandConversionTab(F94): Result={emission_t:.6f} t CH4/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 94")

    def _calculate_f95(self):
        try:
            area = get_float(self.f95_area, "Площадь пожара (Ф.95)")
            fuel_mass = get_float(self.f95_fuel_mass, "Масса топлива (Ф.95)")
            comb_factor = get_float(self.f95_comb_factor, "Коэф. сгорания (Ф.95)")
            gas_type = self.f95_gas_type.currentText()
            # Используем EF для кормовых угодий как наиболее близкие
            ef_value = self.data_service.get_fire_emission_factor('кормовые_угодья', gas_type)
            if ef_value is None: raise ValueError(f"Коэффициент выброса для {gas_type} не найден.")
            emission = self.calculator.calculate_conversion_fire_emissions(area, fuel_mass, comb_factor, ef_value)
            result = f"Выбросы от пожара (Ф. 95) {gas_type}: {emission:.4f} т"
            gwp_factors = {"CO2": 1, "CH4": 28, "N2O": 265}
            gwp = gwp_factors.get(gas_type, 1)
            if gwp != 1: co2_eq = emission * gwp; result += f" (CO2-экв: {co2_eq:.4f} т)"
            self.f95_result.setText(result); logging.info(f"LandConversionTab(F95): Result={emission:.4f} t {gas_type}")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 95")

    def _calculate_f96(self):
        try:
            plant=get_float(self.f96_c_plant,"C растения"); manure=get_float(self.f96_c_manure,"C навоз")
            resp=get_float(self.f96_c_resp,"C дыхание"); erosion=get_float(self.f96_c_erosion,"C эрозия")
            hay=get_float(self.f96_c_hay,"C сено"); feed=get_float(self.f96_c_feed,"C корм"); green=get_float(self.f96_c_green,"C зел.масса")
            delta_c = self.calculator.calculate_grassland_soil_carbon_change(plant, manure, resp, erosion, hay, feed, green)
            co2_eq = delta_c * (-44/12)
            result = (f"ΔC почв корм. угодий (Ф. 96): {delta_c:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.f96_result.setText(result); logging.info(f"LandConversionTab: F96 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 96")

    def _calculate_f97(self):
        try:
            area = get_float(self.f97_area, "Площадь (Ф.97)")
            c_acc = get_float(self.f97_c_acc, "Аккумуляция C (Ф.97)")
            c_plant = self.calculator.calculate_grassland_plant_carbon(area, c_acc)
            self.f96_c_plant.setText(self.c_locale.toString(c_plant, 'f', 4))
            self.f97_result.setText(f"C растения (Ф. 97): {c_plant:.4f} т C/год (подставлено в Ф.96)")
            logging.info(f"LandConversionTab: F97 calculated: {c_plant:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 97")

    def _calculate_f99(self):
        try:
            area = get_float(self.f99_area, "Площадь (Ф.99)")
            factor = get_float(self.f99_erosion_factor, "Коэф. эрозии (Ф.99)")
            c_erosion = self.calculator.calculate_grassland_erosion(area, factor)
            self.f96_c_erosion.setText(self.c_locale.toString(c_erosion, 'f', 4))
            self.f99_result.setText(f"C эрозия (Ф. 99): {c_erosion:.4f} т C/год (подставлено в Ф.96)")
            logging.info(f"LandConversionTab: F99 calculated: {c_erosion:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 99")

    def _calculate_f100(self):
        try:
            hay_yield = get_float(self.f100_hay_yield, "Урожайность сена (Ф.100)")
            carbon_removal = self.calculator.calculate_hay_carbon_removal(hay_yield)
            self.f96_c_hay.setText(self.c_locale.toString(carbon_removal, 'f', 4))
            self.f100_result.setText(f"Вынос C с сеном (Ф. 100): {carbon_removal:.4f} т C/год (подставлено в Ф.96)")
            logging.info(f"LandConversionTab: F100 calculated: {carbon_removal:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 100")



    def _calculate_livestock_manure(self):
        """Расчет C навоза от животных на пастбище (детальный расчет для Ф.98)"""
        try:
            livestock_data_list = []
            for row in range(self.livestock_table.rowCount()):
                animal_type_item = self.livestock_table.item(row, 0)
                count_item = self.livestock_table.item(row, 1)
                excretion_item = self.livestock_table.item(row, 2)
                grazing_time_item = self.livestock_table.item(row, 3)

                if all([animal_type_item, count_item, excretion_item, grazing_time_item]):
                    animal_type = animal_type_item.text().strip()
                    if animal_type:
                        count = int(count_item.text())
                        excretion = float(excretion_item.text().replace(',', '.'))
                        grazing_time = float(grazing_time_item.text().replace(',', '.'))
                        from calculations.absorption_agricultural import LivestockData
                        livestock_data_list.append(LivestockData(
                            animal_type=animal_type,
                            count=count,
                            excretion_factor=excretion,
                            grazing_time=grazing_time
                        ))

            if not livestock_data_list:
                raise ValueError("Добавьте хотя бы один тип животных с данными")

            # Простой расчет: сумма (поголовье * экскреция * время_на_пастбище/100)
            total_manure_c = sum(
                ld.count * ld.excretion_factor * (ld.grazing_time / 100.0)
                for ld in livestock_data_list
            )

            # Подставляем результат в поле Ф.98
            self.f98_manure_c.setText(f"{total_manure_c:.4f}")

            result_text = f"C навоз (детальный расчет): {total_manure_c:.4f} т C/год\n\nРазбивка:\n"
            for ld in livestock_data_list:
                contrib = ld.count * ld.excretion_factor * (ld.grazing_time / 100.0)
                result_text += f"  {ld.animal_type}: {contrib:.4f} т C/год\n"

            self.f98_result.setText(result_text)
            logging.info(f"LandConversionTab(Livestock): Total={total_manure_c:.4f} t C/year")
        except Exception as e:
            handle_error(self, e, "LandConversionTab", "Расчет навоза")

    def get_summary_data(self) -> Dict[str, float]:
        """Собирает данные для сводного отчета."""
        data = {
            'absorption_c': 0.0,
            'emission_co2': 0.0,
            'emission_ch4': 0.0,
            'emission_n2o': 0.0,
            'details': ''
        }
        details = "Конверсия земель и кормовые угодья:\n"

        try:
            # Собираем данные из Ф. 91 (изменение углерода при конверсии)
            if hasattr(self, 'f91_c_after') and self.f91_c_after.text():
                c_after = float(self.f91_c_after.text().replace(',', '.'))
                c_before = float(self.f91_c_before.text().replace(',', '.')) if self.f91_c_before.text() else 0
                c_change = (c_after - c_before)
                if c_change < 0:
                    data['absorption_c'] += abs(c_change)
                details += f"  - Изменение C при конверсии: {c_change:.2f} т C\n"
        except:
            details += "  - Данные Ф. 91 не заполнены\n"

        data['details'] = details
        return data

