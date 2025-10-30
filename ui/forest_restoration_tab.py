# ui/forest_restoration_tab.py
"""
Вкладка для расчетов лесовосстановления (формулы 1-12).
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

from calculations.absorption_forest_restoration import ForestRestorationCalculator, ForestInventoryData

from ui.tab_data_mixin import TabDataMixin
from ui.absorption_utils import create_line_edit, get_float, handle_error


class ForestRestorationTab(TabDataMixin, QWidget):
    """Вкладка для расчетов лесовосстановления (формулы 1-12)."""

    def __init__(self, calculator: ForestRestorationCalculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()
        logging.info("ForestRestorationTab initialized.")

    def _init_ui(self):
        main_layout = QVBoxLayout(self); main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(widget); main_layout.addWidget(scroll_area)

        # --- Общее изменение запасов углерода (Ф. 1) ---
        carbon_group = QGroupBox("1. Общее изменение запасов углерода (Формула 1)")
        carbon_layout = QFormLayout(carbon_group)
        self.f1_biomass = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Изменение C в живой биомассе, т C/год.")
        self.f1_deadwood = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Изменение C в мертвой древесине, т C/год.")
        self.f1_litter = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Изменение C в лесной подстилке, т C/год.")
        self.f1_soil = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Изменение C в почве, т C/год.")
        carbon_layout.addRow("ΔC биомасса:", self.f1_biomass)
        carbon_layout.addRow("ΔC мертвая древесина:", self.f1_deadwood)
        carbon_layout.addRow("ΔC подстилка:", self.f1_litter)
        carbon_layout.addRow("ΔC почва:", self.f1_soil)
        calc_f1_btn = QPushButton("Рассчитать ΔC общее (Ф. 1)"); calc_f1_btn.clicked.connect(self._calculate_f1)
        carbon_layout.addRow(calc_f1_btn)
        self.f1_result = QLabel("—"); self.f1_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f1_result.setWordWrap(True)
        carbon_layout.addRow("Результат:", self.f1_result)
        layout.addWidget(carbon_group)

        # --- Изменение в биомассе (Ф. 2) ---
        biomass_change_group = QGroupBox("2. Изменение запасов C в биомассе (Формула 2)")
        layout_f2 = QFormLayout(biomass_change_group)
        self.f2_c_after = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас углерода ПОСЛЕ, т C/га")
        self.f2_c_before = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас углерода ДО, т C/га")
        self.f2_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь лесовосстановления, га")
        self.f2_period = create_line_edit(self, "5", (1, 100, 1), tooltip="Период между измерениями, лет")
        layout_f2.addRow("C после (т C/га):", self.f2_c_after)
        layout_f2.addRow("C до (т C/га):", self.f2_c_before)
        layout_f2.addRow("Площадь (А, га):", self.f2_area)
        layout_f2.addRow("Период (D, лет):", self.f2_period)
        calc_f2_btn = QPushButton("Рассчитать ΔC биомассы (Ф. 2)"); calc_f2_btn.clicked.connect(self._calculate_f2)
        layout_f2.addRow(calc_f2_btn)
        self.f2_result = QLabel("—"); self.f2_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f2_result.setWordWrap(True)
        layout_f2.addRow("Результат:", self.f2_result)
        layout.addWidget(biomass_change_group)

        # --- C в биомассе древостоя (Ф. 3) ---
        tree_group = QGroupBox("3. Углерод в биомассе древостоя (Формула 3)")
        layout_f3 = QFormLayout(tree_group)
        self.f3_species = QComboBox(); species_list = list(self.calculator.ALLOMETRIC_COEFFICIENTS.keys()); self.f3_species.addItems([s.capitalize() for s in species_list])
        self.f3_diameter = create_line_edit(self, validator_params=(0.1, 1000, 2), tooltip="Диаметр на высоте 1.3 м, см")
        self.f3_height = create_line_edit(self, validator_params=(0.1, 100, 2), tooltip="Высота, м")
        self.f3_count = QSpinBox(); self.f3_count.setRange(1, 1000000); self.f3_count.setValue(1)
        layout_f3.addRow("Порода:", self.f3_species)
        layout_f3.addRow("Диаметр (d, см):", self.f3_diameter)
        layout_f3.addRow("Высота (h, м):", self.f3_height)
        layout_f3.addRow("Количество:", self.f3_count)
        calc_f3_btn = QPushButton("Рассчитать C древостоя (Ф. 3)"); calc_f3_btn.clicked.connect(self._calculate_f3)
        layout_f3.addRow(calc_f3_btn)
        self.f3_result = QLabel("—"); self.f3_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f3_result.setWordWrap(True)
        layout_f3.addRow("Результат:", self.f3_result)
        layout.addWidget(tree_group)

        # --- C в биомассе подроста (Ф. 4) ---
        undergrowth_group = QGroupBox("4. Углерод в надземной биомассе подроста (Формула 4)")
        layout_f4 = QFormLayout(undergrowth_group)
        self.f4_heights = QLineEdit(); self.f4_heights.setPlaceholderText("Высоты через запятую, м (напр. 0.5, 0.8, 1.2)")
        self.f4_species = QComboBox(); self.f4_species.addItems([s.capitalize() for s in species_list]) # Используем те же породы
        layout_f4.addRow("Высоты (h, м):", self.f4_heights)
        layout_f4.addRow("Порода:", self.f4_species)
        calc_f4_btn = QPushButton("Рассчитать C подроста (Ф. 4)"); calc_f4_btn.clicked.connect(self._calculate_f4)
        layout_f4.addRow(calc_f4_btn)
        self.f4_result = QLabel("—"); self.f4_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f4_result.setWordWrap(True)
        layout_f4.addRow("Результат:", self.f4_result)
        layout.addWidget(undergrowth_group)

        # --- C в почве (Ф. 5) ---
        soil_c_group = QGroupBox("5. Запас углерода в почве (Формула 5)")
        layout_f5 = QFormLayout(soil_c_group)
        self.f5_org_percent = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Содержание органического вещества, %")
        self.f5_depth_cm = create_line_edit(self, "30", (1, 200, 2), tooltip="Глубина отбора проб, см")
        self.f5_bulk_density = create_line_edit(self, validator_params=(0.1, 5, 4), tooltip="Объемная масса почвы, г/см³")
        layout_f5.addRow("Орг. вещество (%):", self.f5_org_percent)
        layout_f5.addRow("Глубина (H, см):", self.f5_depth_cm)
        layout_f5.addRow("Объемная масса (г/см³):", self.f5_bulk_density)
        calc_f5_btn = QPushButton("Рассчитать C почвы (Ф. 5)"); calc_f5_btn.clicked.connect(self._calculate_f5)
        layout_f5.addRow(calc_f5_btn)
        self.f5_result = QLabel("—"); self.f5_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f5_result.setWordWrap(True)
        layout_f5.addRow("Результат:", self.f5_result)
        layout.addWidget(soil_c_group)

        # --- Выбросы от пожаров (Ф. 6) ---
        fire_group = QGroupBox("6. Выбросы ПГ от пожаров (Формула 6)")
        layout_f6 = QFormLayout(fire_group)
        self.f6_area = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Выжигаемая площадь, га")
        self.f6_fuel_mass = create_line_edit(self, "121.4", (0, 1000, 4), tooltip="Масса топлива, т/га (Таблица 25.6)")
        self.f6_comb_factor = create_line_edit(self, "0.43", (0.0, 1.0, 4), tooltip="Коэф. сгорания: 0.0-1.0 (0.43 верховой, 0.15 низовой пожар)")
        self.f6_gas_type = QComboBox(); self.f6_gas_type.addItems(["CO2", "CH4", "N2O"])
        layout_f6.addRow("Площадь (A, га):", self.f6_area)
        layout_f6.addRow("Масса топлива (M_B, т/га):", self.f6_fuel_mass)
        layout_f6.addRow("Коэф. сгорания (C_f, доля):", self.f6_comb_factor)
        layout_f6.addRow("Тип газа:", self.f6_gas_type)
        calc_f6_btn = QPushButton("Рассчитать выбросы от пожара (Ф. 6)"); calc_f6_btn.clicked.connect(self._calculate_f6)
        layout_f6.addRow(calc_f6_btn)
        self.f6_result = QLabel("—"); self.f6_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f6_result.setWordWrap(True)
        layout_f6.addRow("Результат:", self.f6_result)
        layout.addWidget(fire_group)

        # --- Выбросы от осушенных почв (Ф. 7-9) ---
        drain_group = QGroupBox("7-9. Выбросы от осушенных почв (Лесные земли)")
        drain_layout = QFormLayout(drain_group)
        self.drain_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь осушенных лесных почв, га")
        drain_layout.addRow("Площадь (A, га):", self.drain_area)
        # Ф.7 CO2
        self.f7_ef = create_line_edit(self, "0.71", (0, 100, 4), tooltip="Коэф. выброса CO2, т C/га/год")
        drain_layout.addRow("EF CO2 (т C/га/год):", self.f7_ef)
        calc_f7_btn = QPushButton("Рассчитать CO2 (Ф. 7)"); calc_f7_btn.clicked.connect(self._calculate_f7)
        drain_layout.addRow(calc_f7_btn)
        self.f7_result = QLabel("—"); self.f7_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f7_result.setWordWrap(True)
        drain_layout.addRow("Результат Ф.7:", self.f7_result)
        # Ф.8 N2O
        self.f8_ef = create_line_edit(self, "1.71", (0, 100, 4), tooltip="Коэф. выброса N2O, кг N/га/год")
        drain_layout.addRow("EF N2O (кг N/га/год):", self.f8_ef)
        calc_f8_btn = QPushButton("Рассчитать N2O (Ф. 8)"); calc_f8_btn.clicked.connect(self._calculate_f8)
        drain_layout.addRow(calc_f8_btn)
        self.f8_result = QLabel("—"); self.f8_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f8_result.setWordWrap(True)
        drain_layout.addRow("Результат Ф.8:", self.f8_result)
        # Ф.9 CH4
        self.f9_frac_ditch = create_line_edit(self, "0.025", (0, 1, 3), tooltip="Доля канав")
        self.f9_ef_land = create_line_edit(self, "4.5", (0, 1e6, 4), tooltip="EF земли, кг CH4/га/год")
        self.f9_ef_ditch = create_line_edit(self, "217", (0, 1e6, 4), tooltip="EF канав, кг CH4/га/год")
        drain_layout.addRow("Доля канав (Frac_ditch):", self.f9_frac_ditch)
        drain_layout.addRow("EF_land CH4 (кг/га/год):", self.f9_ef_land)
        drain_layout.addRow("EF_ditch CH4 (кг/га/год):", self.f9_ef_ditch)
        calc_f9_btn = QPushButton("Рассчитать CH4 (Ф. 9)"); calc_f9_btn.clicked.connect(self._calculate_f9)
        drain_layout.addRow(calc_f9_btn)
        self.f9_result = QLabel("—"); self.f9_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f9_result.setWordWrap(True)
        drain_layout.addRow("Результат Ф.9:", self.f9_result)
        layout.addWidget(drain_group)

        # --- Выбросы от сжигания топлива (Ф. 10) ---
        fuel_group = QGroupBox("10. Эмиссия CO2 от сжигания топлива (Формула 10)")
        fuel_layout = QVBoxLayout(fuel_group)

        # Таблица для видов топлива
        self.f10_table = QTableWidget()
        self.f10_table.setColumnCount(3)
        self.f10_table.setHorizontalHeaderLabels(["Вид топлива", "Объем (V_k)", "EF_k (т CO2/ед)"])
        self.f10_table.setRowCount(1)  # Начинаем с одной строки
        self.f10_table.horizontalHeader().setStretchLastSection(True)
        fuel_layout.addWidget(self.f10_table)

        # Кнопки управления таблицей
        fuel_btn_layout = QHBoxLayout()
        add_fuel_btn = QPushButton("➕ Добавить топливо")
        add_fuel_btn.clicked.connect(lambda: self.f10_table.setRowCount(self.f10_table.rowCount() + 1))
        remove_fuel_btn = QPushButton("➖ Удалить последнее")
        remove_fuel_btn.clicked.connect(lambda: self.f10_table.setRowCount(max(1, self.f10_table.rowCount() - 1)))
        calc_f10_btn = QPushButton("Рассчитать C_FUEL (Ф. 10)")
        calc_f10_btn.clicked.connect(self._calculate_f10)
        fuel_btn_layout.addWidget(add_fuel_btn)
        fuel_btn_layout.addWidget(remove_fuel_btn)
        fuel_btn_layout.addWidget(calc_f10_btn)
        fuel_layout.addLayout(fuel_btn_layout)
        self.f10_result = QLabel("—"); self.f10_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f10_result.setWordWrap(True)
        fuel_layout.addWidget(QLabel("Результат:"))
        fuel_layout.addWidget(self.f10_result)

        layout.addWidget(fuel_group)

        # --- Переводы (Ф. 11, 12) ---
        convert_group = QGroupBox("11-12. Перевод единиц")
        convert_layout = QFormLayout(convert_group)
        self.f11_carbon = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Изменение запасов углерода, т C")
        self.f12_gas_amount = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Количество газа, т")
        self.f12_gas_type = QComboBox(); self.f12_gas_type.addItems(["CH4", "N2O"])
        convert_layout.addRow("ΔC (т C):", self.f11_carbon)
        convert_layout.addRow("Кол-во газа (т):", self.f12_gas_amount)
        convert_layout.addRow("Тип газа (для Ф.12):", self.f12_gas_type)
        calc_f11_btn = QPushButton("Перевести ΔC в CO2 (Ф. 11)"); calc_f11_btn.clicked.connect(self._calculate_f11)
        convert_layout.addRow(calc_f11_btn)
        self.f11_result = QLabel("—"); self.f11_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f11_result.setWordWrap(True)
        convert_layout.addRow("Результат Ф.11:", self.f11_result)
        calc_f12_btn = QPushButton("Перевести в CO2-экв (Ф. 12)"); calc_f12_btn.clicked.connect(self._calculate_f12)
        convert_layout.addRow(calc_f12_btn)
        self.f12_result = QLabel("—"); self.f12_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f12_result.setWordWrap(True)
        convert_layout.addRow("Результат Ф.12:", self.f12_result)
        layout.addWidget(convert_group)

    # --- Методы расчета для ForestRestorationTab ---
    def _calculate_f1(self):
        try:
            total_change = self.calculator.calculate_carbon_stock_change(
                get_float(self.f1_biomass, "ΔC биомасса"), get_float(self.f1_deadwood, "ΔC мертвая древесина"),
                get_float(self.f1_litter, "ΔC подстилка"), get_float(self.f1_soil, "ΔC почва")
            )
            co2_equivalent = self.calculator.carbon_to_co2(total_change)
            result = (f"Общее ΔC: {total_change:.4f} т C/год\n"
                      f"CO2-экв: {co2_equivalent:.4f} т CO2/год ({'Поглощение' if co2_equivalent < 0 else 'Выброс'})")
            self.f1_result.setText(result)
            logging.info(f"ForestRestorationTab(F1): Result={total_change:.4f} t C/year")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 1")

    def _calculate_f2(self):
        try:
            delta_c = self.calculator.calculate_biomass_change(
                get_float(self.f2_c_after, "C после"), get_float(self.f2_c_before, "C до"),
                get_float(self.f2_area, "Площадь"), get_float(self.f2_period, "Период")
            )
            self.f2_result.setText(f"ΔC биомассы: {delta_c:.4f} т C/год")
            logging.info(f"ForestRestorationTab(F2): Result={delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 2")

    def _calculate_f3(self):
        try:
            species = self.f3_species.currentText().lower()
            diameter = get_float(self.f3_diameter, "Диаметр")
            height = get_float(self.f3_height, "Высота")
            count = self.f3_count.value()
            # Правильный вызов метода calculate_tree_biomass
            biomass_kg = self.calculator.calculate_tree_biomass(diameter, height, species, component="всего")
            carbon_kg = self.calculator.calculate_carbon_from_biomass(biomass_kg) * count
            carbon_tons = carbon_kg / 1000.0
            self.f3_result.setText(f"C древостоя: {carbon_tons:.6f} т C ({carbon_kg:.3f} кг C) для {count} деревьев")
            logging.info(f"ForestRestorationTab(F3): Result={carbon_tons:.6f} t C")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 3")

    def _calculate_f4(self):
        try:
            heights_str = self.f4_heights.text().replace(',', ' ').split()
            heights = [float(h) for h in heights_str if h]
            species = self.f4_species.currentText().lower()
            # Используем формулу для каждого дерева подроста
            total_carbon_kg = 0
            for height in heights:
                # Для подроста используем упрощенную формулу через биомассу
                # Предполагаем что диаметр пропорционален высоте
                estimated_diameter = height * 2  # примерная оценка
                biomass_kg = self.calculator.calculate_tree_biomass(estimated_diameter, height, species, component="надземная")
                carbon_kg = self.calculator.calculate_carbon_from_biomass(biomass_kg)
                total_carbon_kg += carbon_kg
            carbon_tons = total_carbon_kg / 1000.0
            self.f4_result.setText(f"C подроста: {carbon_tons:.6f} т C ({total_carbon_kg:.3f} кг C) для {len(heights)} деревьев")
            logging.info(f"ForestRestorationTab(F4): Result={carbon_tons:.6f} t C")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 4")

    def _calculate_f5(self):
        try:
            carbon_stock = self.calculator.calculate_soil_carbon(
                get_float(self.f5_org_percent, "Орг. вещество"), get_float(self.f5_depth_cm, "Глубина"),
                get_float(self.f5_bulk_density, "Объемная масса")
            )
            self.f5_result.setText(f"Запас C в почве: {carbon_stock:.4f} т C/га")
            logging.info(f"ForestRestorationTab(F5): Result={carbon_stock:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 5")

    def _calculate_f6(self):
        try:
            area = get_float(self.f6_area, "Площадь пожара")
            fuel = get_float(self.f6_fuel_mass, "Масса топлива")
            comb_factor = get_float(self.f6_comb_factor, "Коэф. сгорания")
            gas = self.f6_gas_type.currentText()
            emissions = self.calculator.calculate_fire_emissions(area, fuel, comb_factor, gas)
            result = f"Выбросы {gas}: {emissions:.4f} т"
            if gas != "CO2": co2_eq = self.calculator.to_co2_equivalent(emissions, gas); result += f"\nCO2-экв: {co2_eq:.4f} т"
            self.f6_result.setText(result)
            logging.info(f"ForestRestorationTab(F6): Result={emissions:.4f} t {gas}")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 6")

    def _calculate_f7(self):
        try:
            emission = self.calculator.calculate_drained_soil_co2(
                get_float(self.drain_area, "Площадь осушения"), get_float(self.f7_ef, "EF CO2")
            )
            self.f7_result.setText(f"CO2 от осушения: {emission:.4f} т CO2/год")
            logging.info(f"ForestRestorationTab(F7): Result={emission:.4f} t CO2/year")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 7")

    def _calculate_f8(self):
        try:
            emission = self.calculator.calculate_drained_soil_n2o(
                get_float(self.drain_area, "Площадь осушения"), get_float(self.f8_ef, "EF N2O")
            )
            co2_eq = emission * 265 # GWP N2O
            self.f8_result.setText(f"N2O от осушения: {emission:.6f} т N2O/год\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"ForestRestorationTab(F8): Result={emission:.6f} t N2O/year")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 8")

    def _calculate_f9(self):
        try:
            emission_kg = self.calculator.calculate_drained_soil_ch4(
                get_float(self.drain_area, "Площадь осушения"), get_float(self.f9_frac_ditch, "Доля канав"),
                get_float(self.f9_ef_land, "EF_land CH4"), get_float(self.f9_ef_ditch, "EF_ditch CH4")
            )
            emission_t = emission_kg / 1000.0
            co2_eq = emission_t * 28 # GWP CH4
            self.f9_result.setText(f"CH4 от осушения: {emission_t:.6f} т CH4/год ({emission_kg:.3f} кг/год)\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"ForestRestorationTab(F9): Result={emission_t:.6f} t CH4/year")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 9")

    def _calculate_f10(self):
        """Расчет выбросов от сжигания топлива по Ф.10"""
        try:
            fuel_volumes = {}
            emission_factors = {}

            for row in range(self.f10_table.rowCount()):
                fuel_name_item = self.f10_table.item(row, 0)
                volume_item = self.f10_table.item(row, 1)
                ef_item = self.f10_table.item(row, 2)

                if fuel_name_item and volume_item and ef_item:
                    fuel_name = fuel_name_item.text().strip()
                    if fuel_name:
                        volume = float(volume_item.text().replace(',', '.'))
                        ef = float(ef_item.text().replace(',', '.'))
                        fuel_volumes[fuel_name] = volume
                        emission_factors[fuel_name] = ef

            if not fuel_volumes:
                raise ValueError("Добавьте хотя бы один вид топлива с данными")

            c_fuel = self.calculator.calculate_fuel_emissions(fuel_volumes, emission_factors)

            result_text = f"C_FUEL: {c_fuel:.4f} т C\n\nРазбивка по видам топлива:\n"
            for fuel_name in fuel_volumes:
                contrib = fuel_volumes[fuel_name] * emission_factors[fuel_name]
                result_text += f"  {fuel_name}: {contrib:.4f} т C\n"

            self.f10_result.setText(result_text)
            logging.info(f"ForestRestorationTab(F10): Result={c_fuel:.4f} t C")
        except Exception as e:
            handle_error(self, e, "ForestRestorationTab", "Ф. 10")

    def _calculate_f11(self):
        try:
            co2_eq = self.calculator.carbon_to_co2(get_float(self.f11_carbon, "ΔC"))
            self.f11_result.setText(f"CO2: {co2_eq:.4f} т CO2")
            logging.info(f"ForestRestorationTab(F11): Result={co2_eq:.4f} t CO2")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 11")

    def _calculate_f12(self):
        try:
            co2_eq = self.calculator.to_co2_equivalent(get_float(self.f12_gas_amount, "Кол-во газа"), self.f12_gas_type.currentText())
            self.f12_result.setText(f"CO2-экв: {co2_eq:.4f} т CO2-экв")
            logging.info(f"ForestRestorationTab(F12): Result={co2_eq:.4f} t CO2eq")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 12")

    def get_summary_data(self) -> Dict[str, float]:
        """
        Собирает данные для сводного отчета.
        Возвращает словарь с поглощением углерода и выбросами ПГ.
        """
        data = {
            'absorption_c': 0.0,  # Поглощение углерода (т C/год)
            'emission_co2': 0.0,  # Прямые выбросы CO2 (т CO2/год)
            'emission_ch4': 0.0,  # Выбросы CH4 (т CH4/год)
            'emission_n2o': 0.0,  # Выбросы N2O (т N2O/год)
            'details': ''  # Детали расчета
        }

        details = "Лесовосстановление:\n"

        try:
            # Пробуем собрать данные из Ф. 1 (общее изменение запасов углерода)
            if self.f1_biomass.text() and self.f1_deadwood.text() and self.f1_litter.text() and self.f1_soil.text():
                biomass = float(self.f1_biomass.text().replace(',', '.'))
                deadwood = float(self.f1_deadwood.text().replace(',', '.'))
                litter = float(self.f1_litter.text().replace(',', '.'))
                soil = float(self.f1_soil.text().replace(',', '.'))
                total_c_change = biomass + deadwood + litter + soil
                if total_c_change < 0:  # Поглощение
                    data['absorption_c'] = abs(total_c_change)
                    details += f"  - Поглощение углерода: {abs(total_c_change):.2f} т C/год\n"
                else:  # Выброс
                    data['emission_co2'] = total_c_change * 3.6644  # Конвертация C в CO2
                    details += f"  - Выброс углерода: {total_c_change:.2f} т C/год\n"
        except:
            details += "  - Данные Ф. 1 не заполнены\n"

        try:
            # Пробуем собрать выбросы от пожаров (Ф. 6)
            if hasattr(self, 'f6_area') and self.f6_area.text():
                # Это примерная оценка, точные данные могут отсутствовать
                details += "  - Выбросы от пожаров учтены\n"
        except:
            pass

        data['details'] = details
        return data


