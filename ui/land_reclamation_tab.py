# ui/land_reclamation_tab.py
"""
Вкладка для расчетов поглощения при рекультивации земель.
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

from calculations.absorption_forest_restoration import LandReclamationCalculator
from data_models_extended import DataService

from ui.tab_data_mixin import TabDataMixin
from ui.absorption_utils import create_line_edit, get_float, handle_error


class LandReclamationTab(TabDataMixin, QWidget):
    """Вкладка для расчетов по рекультивации земель (Формулы 13-26)."""
    def __init__(self, calculator: LandReclamationCalculator, data_service: DataService, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.data_service = data_service
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()
        logging.info("LandReclamationTab initialized.")

    def _init_ui(self):
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget); main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(main_widget)
        outer_layout = QVBoxLayout(self); outer_layout.addWidget(scroll_area)

        # --- Изменение запасов C (Ф. 13-15) ---
        change_group = QGroupBox("Изменение запасов углерода (Формулы 13-15)")
        change_layout = QVBoxLayout(change_group)
        params_layout = QFormLayout()
        self.f14_15_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь рекультивации, га")
        self.f14_15_period = create_line_edit(self, "1", (0.1, 100, 2), tooltip="Период между измерениями запасов, лет")
        params_layout.addRow("Площадь (A_рек, га):", self.f14_15_area)
        params_layout.addRow("Период (D, лет):", self.f14_15_period)
        change_layout.addLayout(params_layout)
        layout_f14 = QFormLayout()
        self.f14_c_after = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас C в биомассе ПОСЛЕ рекультивации, т C/га")
        self.f14_c_before = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас C в биомассе ДО рекультивации, т C/га")
        layout_f14.addRow("C биомассы ПОСЛЕ (т C/га):", self.f14_c_after)
        layout_f14.addRow("C биомассы ДО (т C/га):", self.f14_c_before)
        calc_f14_btn = QPushButton("Рассчитать ΔC биомассы (Ф. 14)"); calc_f14_btn.clicked.connect(self._calculate_f14)
        layout_f14.addRow(calc_f14_btn)
        self.f14_result = QLabel("—"); self.f14_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f14_result.setWordWrap(True)
        layout_f14.addRow("Результат:", self.f14_result)
        change_layout.addLayout(layout_f14)
        layout_f15 = QFormLayout()
        self.f15_soil_after = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас C в почве ПОСЛЕ рекультивации, т C/га")
        self.f15_soil_before = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас C в почве ДО рекультивации, т C/га")
        layout_f15.addRow("C почвы ПОСЛЕ (т C/га):", self.f15_soil_after)
        layout_f15.addRow("C почвы ДО (т C/га):", self.f15_soil_before)
        calc_f15_btn = QPushButton("Рассчитать ΔC почвы (Ф. 15)"); calc_f15_btn.clicked.connect(self._calculate_f15)
        layout_f15.addRow(calc_f15_btn)
        self.f15_result = QLabel("—"); self.f15_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f15_result.setWordWrap(True)
        layout_f15.addRow("Результат:", self.f15_result)
        change_layout.addLayout(layout_f15)
        layout_f13 = QFormLayout()
        self.f13_biomass_change_res = QLineEdit(); self.f13_biomass_change_res.setReadOnly(True); self.f13_biomass_change_res.setPlaceholderText("Результат Ф.14")
        self.f13_soil_change_res = QLineEdit(); self.f13_soil_change_res.setReadOnly(True); self.f13_soil_change_res.setPlaceholderText("Результат Ф.15")
        layout_f13.addRow("ΔC биомасса (т C/год):", self.f13_biomass_change_res)
        layout_f13.addRow("ΔC почва (т C/год):", self.f13_soil_change_res)
        calc_f13_btn = QPushButton("Рассчитать ΔC рекультивации (Ф. 13)"); calc_f13_btn.clicked.connect(self._calculate_f13)
        layout_f13.addRow(calc_f13_btn)
        self.f13_result = QLabel("—"); self.f13_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f13_result.setWordWrap(True)
        layout_f13.addRow("Результат:", self.f13_result)
        change_layout.addLayout(layout_f13)
        main_layout.addWidget(change_group)

        # --- Углерод в травянистой биомассе (Ф. 20-22) ---
        grass_group = QGroupBox("Углерод в травянистой биомассе (Формулы 20-22)")
        grass_layout = QVBoxLayout(grass_group)
        layout_f21 = QFormLayout()
        self.f21_dry_weight = create_line_edit(self, validator_params=(0, 1e6, 4), tooltip="Абсолютно сухой вес пробы травы с площадки 0.04 га?, кг")
        layout_f21.addRow("Сухой вес пробы (кг):", self.f21_dry_weight)
        calc_f21_btn = QPushButton("Рассчитать C надземной биомассы (Ф. 21)"); calc_f21_btn.clicked.connect(self._calculate_f21)
        layout_f21.addRow(calc_f21_btn)
        self.f21_result = QLabel("—"); self.f21_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f21_result.setWordWrap(True)
        layout_f21.addRow("Результат:", self.f21_result)
        grass_layout.addLayout(layout_f21)
        layout_f22 = QFormLayout()
        self.f22_aboveground_c = create_line_edit(self, validator_params=(0, 1e6, 4), tooltip="Углерод надземной биомассы (из Ф.21), т C/га")
        self.f22_a = create_line_edit(self, "0.922", validator_params=(0, 10, 4))
        self.f22_b = create_line_edit(self, "1.057", validator_params=(0, 10, 4))
        layout_f22.addRow("C надземной (т C/га):", self.f22_aboveground_c)
        layout_f22.addRow("Коэффициент a:", self.f22_a)
        layout_f22.addRow("Коэффициент b:", self.f22_b)
        calc_f22_btn = QPushButton("Рассчитать C подземной биомассы (Ф. 22)"); calc_f22_btn.clicked.connect(self._calculate_f22)
        layout_f22.addRow(calc_f22_btn)
        self.f22_result = QLabel("—"); self.f22_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f22_result.setWordWrap(True)
        layout_f22.addRow("Результат:", self.f22_result)
        grass_layout.addLayout(layout_f22)
        layout_f20 = QFormLayout()
        self.f20_aboveground_res = QLineEdit(); self.f20_aboveground_res.setReadOnly(True); self.f20_aboveground_res.setPlaceholderText("Результат Ф.21")
        self.f20_belowground_res = QLineEdit(); self.f20_belowground_res.setReadOnly(True); self.f20_belowground_res.setPlaceholderText("Результат Ф.22")
        layout_f20.addRow("C надземной (т C/га):", self.f20_aboveground_res)
        layout_f20.addRow("C подземной (т C/га):", self.f20_belowground_res)
        calc_f20_btn = QPushButton("Рассчитать общий C трав. биомассы (Ф. 20)"); calc_f20_btn.clicked.connect(self._calculate_f20)
        layout_f20.addRow(calc_f20_btn)
        self.f20_result = QLabel("—"); self.f20_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f20_result.setWordWrap(True)
        layout_f20.addRow("Результат:", self.f20_result)
        grass_layout.addLayout(layout_f20)
        main_layout.addWidget(grass_group)

        # --- Углерод в почве (Ф. 23) ---
        soil_c_group = QGroupBox("Запас углерода в почве (Формула 23 / 5)")
        layout_f23 = QFormLayout(soil_c_group)
        self.f23_org_percent = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Содержание органического вещества, %")
        self.f23_depth_cm = create_line_edit(self, "30", (1, 200, 2), tooltip="Глубина отбора проб, см")
        self.f23_bulk_density = create_line_edit(self, validator_params=(0.1, 5, 4), tooltip="Объемная масса почвы, г/см³")
        layout_f23.addRow("Орг. вещество (%):", self.f23_org_percent)
        layout_f23.addRow("Глубина (H, см):", self.f23_depth_cm)
        layout_f23.addRow("Объемная масса (г/см³):", self.f23_bulk_density)
        calc_f23_btn = QPushButton("Рассчитать запас C в почве (Ф. 23)"); calc_f23_btn.clicked.connect(self._calculate_f23)
        layout_f23.addRow(calc_f23_btn)
        self.f23_result = QLabel("—"); self.f23_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f23_result.setWordWrap(True)
        layout_f23.addRow("Результат:", self.f23_result)
        main_layout.addWidget(soil_c_group)

        # --- Выбросы от сжигания топлива (Ф. 24) ---
        fuel_group = QGroupBox("24. Эмиссия CO2 от сжигания топлива (Формула 24)")
        fuel_layout = QVBoxLayout(fuel_group)

        # Таблица для видов топлива (аналогично Ф.10)
        self.f24_table = QTableWidget()
        self.f24_table.setColumnCount(3)
        self.f24_table.setHorizontalHeaderLabels(["Вид топлива", "Объем (V_k)", "EF_k (т C/ед)"])
        self.f24_table.setRowCount(1)
        self.f24_table.horizontalHeader().setStretchLastSection(True)
        fuel_layout.addWidget(self.f24_table)

        # Кнопки управления таблицей
        f24_btn_layout = QHBoxLayout()
        add_f24_btn = QPushButton("➕ Добавить топливо")
        add_f24_btn.clicked.connect(lambda: self.f24_table.setRowCount(self.f24_table.rowCount() + 1))
        remove_f24_btn = QPushButton("➖ Удалить последнее")
        remove_f24_btn.clicked.connect(lambda: self.f24_table.setRowCount(max(1, self.f24_table.rowCount() - 1)))
        calc_f24_btn = QPushButton("Рассчитать C_FUEL (Ф. 24)")
        calc_f24_btn.clicked.connect(self._calculate_f24)
        f24_btn_layout.addWidget(add_f24_btn)
        f24_btn_layout.addWidget(remove_f24_btn)
        f24_btn_layout.addWidget(calc_f24_btn)
        fuel_layout.addLayout(f24_btn_layout)
        self.f24_result = QLabel("—"); self.f24_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f24_result.setWordWrap(True)
        fuel_layout.addWidget(QLabel("Результат:"))
        fuel_layout.addWidget(self.f24_result)

        main_layout.addWidget(fuel_group)

        # --- Переводы (Ф. 25, 26) ---
        convert_group = QGroupBox("25-26. Перевод единиц")
        convert_layout = QFormLayout(convert_group)
        self.f25_carbon = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Изменение запасов углерода (из Ф.13), т C")
        self.f26_gas_amount = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Количество газа (CH4 или N2O), т")
        self.f26_gas_type = QComboBox(); self.f26_gas_type.addItems(["CH4", "N2O"])
        convert_layout.addRow("ΔC (т C):", self.f25_carbon)
        convert_layout.addRow("Кол-во газа (т):", self.f26_gas_amount)
        convert_layout.addRow("Тип газа (для Ф.26):", self.f26_gas_type)
        calc_f25_btn = QPushButton("Перевести ΔC в CO2 (Ф. 25)"); calc_f25_btn.clicked.connect(self._calculate_f25)
        convert_layout.addRow(calc_f25_btn)
        self.f25_result = QLabel("—"); self.f25_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f25_result.setWordWrap(True)
        convert_layout.addRow("Результат Ф.25:", self.f25_result)
        calc_f26_btn = QPushButton("Перевести в CO2-экв (Ф. 26)"); calc_f26_btn.clicked.connect(self._calculate_f26)
        convert_layout.addRow(calc_f26_btn)
        self.f26_result = QLabel("—"); self.f26_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f26_result.setWordWrap(True)
        convert_layout.addRow("Результат Ф.26:", self.f26_result)
        main_layout.addWidget(convert_group)

    # --- Методы расчета для LandReclamationTab ---
    def _calculate_f14(self):
        try:
            c_after = get_float(self.f14_c_after, "C биомассы ПОСЛЕ (Ф.14)"); c_before = get_float(self.f14_c_before, "C биомассы ДО (Ф.14)")
            area = get_float(self.f14_15_area, "Площадь (Ф.14)"); period = get_float(self.f14_15_period, "Период (Ф.14)")
            delta_c = self.calculator.calculate_reclamation_biomass_change(c_after, c_before, area, period)
            self.f13_biomass_change_res.setText(f"{delta_c:.4f}")
            self.f14_result.setText(f"ΔC биомассы: {delta_c:.4f} т C/год")
            logging.info(f"LandReclamationTab: F14 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 14")

    def _calculate_f15(self):
        try:
            soil_after = get_float(self.f15_soil_after, "C почвы ПОСЛЕ (Ф.15)"); soil_before = get_float(self.f15_soil_before, "C почвы ДО (Ф.15)")
            area = get_float(self.f14_15_area, "Площадь (Ф.15)"); period = get_float(self.f14_15_period, "Период (Ф.15)")
            delta_c = self.calculator.calculate_reclamation_soil_change(soil_after, soil_before, area, period)
            self.f13_soil_change_res.setText(f"{delta_c:.4f}")
            self.f15_result.setText(f"ΔC почвы: {delta_c:.4f} т C/год")
            logging.info(f"LandReclamationTab: F15 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 15")

    def _calculate_f13(self):
        try:
            biomass_change = get_float(self.f13_biomass_change_res, "ΔC биомасса (из Ф.14)")
            soil_change = get_float(self.f13_soil_change_res, "ΔC почва (из Ф.15)")
            delta_c = self.calculator.calculate_conversion_carbon_change(biomass_change, soil_change) # Метод калькулятора назван так
            co2_eq = delta_c * (-44/12)
            result = (f"ΔC рекультивации:\nΔC = {delta_c:.4f} т C/год\nCO2-экв: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.f13_result.setText(result)
            logging.info(f"LandReclamationTab: F13 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 13")

    def _calculate_f21(self):
        try:
            dry_weight = get_float(self.f21_dry_weight, "Сухой вес пробы (Ф.21)")
            carbon = self.calculator.calculate_aboveground_grass_carbon(dry_weight)
            self.f20_aboveground_res.setText(f"{carbon:.4f}") # Помещаем результат в поле для Ф.20
            self.f22_aboveground_c.setText(f"{carbon:.4f}") # И в поле для Ф.22
            self.f21_result.setText(f"C надземной биомассы: {carbon:.4f} т C/га")
            logging.info(f"LandReclamationTab: F21 calculated: {carbon:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 21")

    def _calculate_f22(self):
        try:
            above_c = get_float(self.f22_aboveground_c, "C надземной (Ф.22)")
            a = get_float(self.f22_a, "Коэффициент a (Ф.22)")
            b = get_float(self.f22_b, "Коэффициент b (Ф.22)")
            carbon = self.calculator.calculate_belowground_grass_carbon(above_c, a, b)
            self.f20_belowground_res.setText(f"{carbon:.4f}") # Помещаем результат в поле для Ф.20
            self.f22_result.setText(f"C подземной биомассы: {carbon:.4f} т C/га")
            logging.info(f"LandReclamationTab: F22 calculated: {carbon:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 22")

    def _calculate_f20(self):
        try:
            above_c = get_float(self.f20_aboveground_res, "C надземной (из Ф.21)")
            below_c = get_float(self.f20_belowground_res, "C подземной (из Ф.22)")
            total_c = self.calculator.calculate_grassland_carbon(above_c, below_c)
            self.f20_result.setText(f"Общий C трав. биомассы: {total_c:.4f} т C/га")
            logging.info(f"LandReclamationTab: F20 calculated: {total_c:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 20")

    def _calculate_f23(self):
        try:
            org_perc = get_float(self.f23_org_percent, "Орг. вещество (Ф.23)"); depth = get_float(self.f23_depth_cm, "Глубина (Ф.23)"); density = get_float(self.f23_bulk_density, "Объемная масса (Ф.23)")
            carbon_stock = self.calculator.calculate_soil_carbon_from_organic(org_perc, depth, density)
            self.f23_result.setText(f"Запас C в почве: {carbon_stock:.4f} т C/га")
            logging.info(f"LandReclamationTab: F23 calculated: {carbon_stock:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 23")

    def _calculate_f24(self):
        """Расчет выбросов от сжигания топлива по Ф.24"""
        try:
            fuel_data = []
            for row in range(self.f24_table.rowCount()):
                fuel_name_item = self.f24_table.item(row, 0)
                volume_item = self.f24_table.item(row, 1)
                ef_item = self.f24_table.item(row, 2)

                if fuel_name_item and volume_item and ef_item:
                    fuel_name = fuel_name_item.text().strip()
                    if fuel_name:
                        volume = float(volume_item.text().replace(',', '.'))
                        ef = float(ef_item.text().replace(',', '.'))
                        fuel_data.append((volume, ef))

            if not fuel_data:
                raise ValueError("Добавьте хотя бы один вид топлива с данными")

            c_fuel = self.calculator.calculate_fossil_fuel_emissions(fuel_data)

            result_text = f"C_FUEL: {c_fuel:.4f} т C\n\nРазбивка по топливу:\n"
            for i, (volume, ef) in enumerate(fuel_data, 1):
                contrib = volume * ef
                result_text += f"  Топливо {i}: {contrib:.4f} т C\n"

            self.f24_result.setText(result_text)
            logging.info(f"LandReclamationTab(F24): Result={c_fuel:.4f} t C")
        except Exception as e:
            handle_error(self, e, "LandReclamationTab", "Ф. 24")

    def _calculate_f25(self):
        try:
            co2_eq = self.calculator.carbon_to_co2_conversion(get_float(self.f25_carbon, "ΔC (Ф.25)"))
            self.f25_result.setText(f"CO2: {co2_eq:.4f} т CO2")
            logging.info(f"LandReclamationTab(F25): Result={co2_eq:.4f} t CO2")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 25")

    def _calculate_f26(self):
        try:
            co2_eq = self.calculator.ghg_to_co2_equivalent(get_float(self.f26_gas_amount, "Кол-во газа (Ф.26)"), self.f26_gas_type.currentText())
            self.f26_result.setText(f"CO2-экв: {co2_eq:.4f} т CO2-экв")
            logging.info(f"LandReclamationTab(F26): Result={co2_eq:.4f} t CO2eq")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 26")

    def get_summary_data(self) -> Dict[str, float]:
        """Собирает данные для сводного отчета."""
        data = {
            'absorption_c': 0.0,
            'emission_co2': 0.0,
            'emission_ch4': 0.0,
            'emission_n2o': 0.0,
            'details': ''
        }
        details = "Рекультивация земель:\n"

        try:
            # Собираем данные из Ф. 20 (углерод травянистой биомассы)
            if hasattr(self, 'f20_above') and self.f20_above.text() and self.f20_below.text():
                above = float(self.f20_above.text().replace(',', '.'))
                below = float(self.f20_below.text().replace(',', '.'))
                total_c = above + below
                data['absorption_c'] += abs(total_c) if total_c < 0 else 0
                details += f"  - Углерод в биомассе: {total_c:.2f} т C\n"
        except:
            details += "  - Данные Ф. 20 не заполнены\n"

        data['details'] = details
        return data


