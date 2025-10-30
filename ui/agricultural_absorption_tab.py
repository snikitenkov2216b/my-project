# ui/agricultural_absorption_tab.py
"""
Вкладка для расчетов поглощения на сельскохозяйственных землях.
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

from calculations.absorption_agricultural import AgriculturalLandCalculator, CropData, LivestockData
from data_models_extended import DataService

from ui.tab_data_mixin import TabDataMixin
from ui.absorption_utils import create_line_edit, get_float, handle_error


class AgriculturalAbsorptionTab(TabDataMixin, QWidget):
    """Вкладка для расчетов поглощения ПГ сельхозугодьями (формулы 75-90)."""

    def __init__(self, calculator: AgriculturalLandCalculator, data_service: DataService, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.data_service = data_service
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()
        logging.info("AgriculturalAbsorptionTab initialized.")

    def _init_ui(self):
        # ... (Код UI для этой вкладки остается без изменений, как в предыдущих ответах) ...
        main_layout = QVBoxLayout(self); main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        tabs = QTabWidget()
        tabs.addTab(self._create_mineral_soil_tab(), "Мин. почвы (Ф. 80-86)")
        tabs.addTab(self._create_organic_soil_tab(), "Орган. почвы (Ф. 75, 87-89)")
        tabs.addTab(self._create_biomass_fire_tab(), "Биомасса и пожары (Ф. 76-79, 90)")
        main_layout.addWidget(tabs)

    def _create_mineral_soil_tab(self):
        widget = QWidget(); layout = QFormLayout(widget)
        self.mineral_c_fert = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Углерод от удобрений (Ф.81)")
        layout.addRow("C от удобрений (т C/год):", self.mineral_c_fert)
        self.mineral_c_lime = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Углерод от извести (Ф.82)")
        layout.addRow("C от извести (т C/год):", self.mineral_c_lime)
        self.mineral_c_plant = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Углерод от растений (Ф.83)")
        layout.addRow("C от растений (т C/год):", self.mineral_c_plant)
        self.mineral_c_resp = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери C от дыхания (Ф.86)")
        layout.addRow("C потери (дыхание) (т C/год):", self.mineral_c_resp)
        self.mineral_c_erosion = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери C от эрозии (Ф.85)")
        layout.addRow("C потери (эрозия) (т C/год):", self.mineral_c_erosion)
        calc_btn = QPushButton("Рассчитать ΔC мин. почв (Ф. 80)"); calc_btn.clicked.connect(self._calculate_mineral_soil_change)
        layout.addRow(calc_btn)
        self.f80_result = QLabel("—")
        self.f80_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f80_result.setWordWrap(True)
        layout.addRow("Результат:", self.f80_result)
        lime_group = QGroupBox("Расчет C от извести (Формула 82)"); lime_layout = QFormLayout(lime_group)
        self.lime_amount = create_line_edit(self, validator_params=(0, 1e9, 4))
        lime_layout.addRow("Кол-во извести (т/год):", self.lime_amount)
        lime_calc_btn = QPushButton("Рассчитать C извести -> подставить выше"); lime_calc_btn.clicked.connect(self._calculate_lime_carbon_helper)
        lime_layout.addRow(lime_calc_btn)
        self.f82_result = QLabel("—")
        self.f82_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f82_result.setWordWrap(True)
        lime_layout.addRow("Результат:", self.f82_result)
        layout.addRow(lime_group)
        erosion_group = QGroupBox("Расчет потерь от эрозии (Формула 85)"); erosion_layout = QFormLayout(erosion_group)
        self.erosion_area = create_line_edit(self, validator_params=(0, 1e12, 4))
        erosion_layout.addRow("Площадь эрозии (га):", self.erosion_area)
        self.erosion_factor = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Коэффициент эрозии, т C/га/год")
        erosion_layout.addRow("Коэф. эрозии (т C/га/год):", self.erosion_factor)
        erosion_calc_btn = QPushButton("Рассчитать C эрозии -> подставить выше"); erosion_calc_btn.clicked.connect(self._calculate_erosion_helper)
        erosion_layout.addRow(erosion_calc_btn)
        self.f85_result = QLabel("—")
        self.f85_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f85_result.setWordWrap(True)
        erosion_layout.addRow("Результат:", self.f85_result)
        layout.addRow(erosion_group)
        # Добавляем расчет для Ф.86
        resp_group = QGroupBox("Расчет потерь от дыхания почвы (Формула 86)")
        resp_layout = QFormLayout(resp_group)
        self.f86_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь участка, га")
        self.f86_rate = create_line_edit(self, validator_params=(0, 5000, 4), tooltip="Скорость эмиссии CO2, мг CO2/м²/час (Таблица 27.2)")
        self.f86_period = create_line_edit(self, "150", (1, 366, 1), tooltip="Длительность вегетационного периода, дни")
        resp_layout.addRow("Площадь (га):", self.f86_area)
        resp_layout.addRow("Скорость эмиссии (мг/м²/час):", self.f86_rate)
        resp_layout.addRow("Вег. период (дни):", self.f86_period)
        calc_f86_btn = QPushButton("Рассчитать C дыхания -> подставить выше"); calc_f86_btn.clicked.connect(self._calculate_respiration_helper)
        resp_layout.addRow(calc_f86_btn)
        self.f86_result = QLabel("—")
        self.f86_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f86_result.setWordWrap(True)
        resp_layout.addRow("Результат:", self.f86_result)
        layout.addRow(resp_group)

        return widget

    def _create_organic_soil_tab(self):
        # ... (Код без изменений) ...
        widget = QWidget(); layout = QFormLayout(widget)
        self.organic_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь осушенных органогенных почв на пахотных землях.")
        layout.addRow("Площадь осушенных почв (га):", self.organic_area)
        calc_co2_btn = QPushButton("Рассчитать выбросы CO2 (Ф. 87)"); calc_co2_btn.clicked.connect(self._calculate_organic_co2)
        layout.addRow(calc_co2_btn)
        self.f87_result = QLabel("—")
        self.f87_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f87_result.setWordWrap(True)
        layout.addRow("Результат:", self.f87_result)
        calc_n2o_btn = QPushButton("Рассчитать выбросы N2O (Ф. 88)"); calc_n2o_btn.clicked.connect(self._calculate_organic_n2o)
        layout.addRow(calc_n2o_btn)
        self.f88_result = QLabel("—")
        self.f88_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f88_result.setWordWrap(True)
        layout.addRow("Результат:", self.f88_result)
        ch4_group = QGroupBox("Параметры для CH4 (Формула 75/89)"); ch4_layout = QFormLayout(ch4_group)
        self.organic_ch4_frac_ditch = create_line_edit(self, "0.5", (0, 1, 3))
        ch4_layout.addRow("Доля канав (Frac_ditch):", self.organic_ch4_frac_ditch)
        self.organic_ch4_ef_land = create_line_edit(self, "0.0", (0, 1e6, 4), tooltip="Для пашни = 0")
        ch4_layout.addRow("EF земли (кг CH4/га/год):", self.organic_ch4_ef_land)
        self.organic_ch4_ef_ditch = create_line_edit(self, "1165", (0, 1e6, 4), tooltip="Для пашни = 1165")
        ch4_layout.addRow("EF канав (кг CH4/га/год):", self.organic_ch4_ef_ditch)
        layout.addRow(ch4_group)
        calc_ch4_btn = QPushButton("Рассчитать выбросы CH4 (Ф. 75/89)"); calc_ch4_btn.clicked.connect(self._calculate_organic_ch4)
        layout.addRow(calc_ch4_btn)
        self.f89_result = QLabel("—")
        self.f89_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f89_result.setWordWrap(True)
        layout.addRow("Результат:", self.f89_result)
        return widget

    def _create_biomass_fire_tab(self):
        # ... (Код без изменений) ...
        widget = QWidget(); layout = QFormLayout(widget)
        biomass_group = QGroupBox("Изменение запасов C в биомассе (Формулы 77-79)"); biomass_layout = QFormLayout(biomass_group)
        self.biomass_gain = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Общий прирост углерода, т C/год")
        biomass_layout.addRow("Прирост C (ΔC_G, т C/год):", self.biomass_gain)
        self.biomass_loss = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Общие потери углерода, т C/год")
        biomass_layout.addRow("Потери C (ΔC_L, т C/год):", self.biomass_loss)
        calc_biomass_btn = QPushButton("Рассчитать ΔC биомассы (Ф. 77)"); calc_biomass_btn.clicked.connect(self._calculate_biomass_change)
        biomass_layout.addRow(calc_biomass_btn)
        self.f77_result = QLabel("—")
        self.f77_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f77_result.setWordWrap(True)
        biomass_layout.addRow("Результат:", self.f77_result)
        layout.addRow(biomass_group)
        fire_group = QGroupBox("Выбросы от пожаров на сельхозземлях (Формула 76/90)"); fire_layout = QFormLayout(fire_group)
        self.agri_fire_area = create_line_edit(self, validator_params=(0, 1e12, 4))
        fire_layout.addRow("Площадь пожара (га):", self.agri_fire_area)
        self.agri_fire_biomass = create_line_edit(self, "10.0", (0, 1000, 4), tooltip="Масса сгораемой биомассы, т/га")
        fire_layout.addRow("Масса биомассы (т/га):", self.agri_fire_biomass)
        self.agri_fire_comb_factor = create_line_edit(self, "0.8", (0.01, 1.0, 3), tooltip="Коэффициент сгорания (доля)")
        fire_layout.addRow("Коэф. сгорания (доля):", self.agri_fire_comb_factor)
        self.agri_fire_gas_type = QComboBox()
        gas_factors = self.data_service.fire_emission_factors.get('сельхоз_остатки', {}); self.agri_fire_gas_type.addItems(gas_factors.keys())
        fire_layout.addRow("Тип газа:", self.agri_fire_gas_type)
        calc_fire_btn = QPushButton("Рассчитать выброс от пожара (Ф. 76/90)"); calc_fire_btn.clicked.connect(self._calculate_agricultural_fire)
        fire_layout.addRow(calc_fire_btn)
        self.f90_result = QLabel("—")
        self.f90_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f90_result.setWordWrap(True)
        fire_layout.addRow("Результат:", self.f90_result)
        layout.addRow(fire_group)
        return widget

    # --- Методы расчета для AgriculturalAbsorptionTab ---
    def _calculate_mineral_soil_change(self):
        try:
            c_fert=get_float(self.mineral_c_fert, "C от удобрений"); c_lime=get_float(self.mineral_c_lime, "C от извести"); c_plant=get_float(self.mineral_c_plant, "C от растений"); c_resp=get_float(self.mineral_c_resp, "C потери (дыхание)"); c_erosion=get_float(self.mineral_c_erosion, "C потери (эрозия)")
            delta_c = self.calculator.calculate_mineral_soil_carbon_change(c_fertilizer=c_fert, c_lime=c_lime, c_plant=c_plant, c_respiration=c_resp, c_erosion=c_erosion)
            co2_eq = delta_c * (-44/12)
            result = (f"ΔC в мин. почвах (Ф. 80): {delta_c:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.f80_result.setText(result); logging.info(f"AgriTab: Mineral soil ΔC calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 80")

    def _calculate_lime_carbon_helper(self):
        try:
            lime_amount = get_float(self.lime_amount, "Кол-во извести"); c_lime = self.calculator.calculate_lime_carbon(lime_amount)
            self.mineral_c_lime.setText(self.c_locale.toString(c_lime, 'f', 4)); self.f82_result.setText(f"C от извести (Ф. 82): {c_lime:.4f} т C/год (подставлено в поле выше)"); logging.info(f"AgriTab: Lime carbon calculated: {c_lime:.4f} t C/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 82 (helper)")

    def _calculate_erosion_helper(self):
        try:
            area = get_float(self.erosion_area, "Площадь эрозии"); factor = get_float(self.erosion_factor, "Коэф. эрозии"); c_erosion = self.calculator.calculate_erosion_losses(area, factor)
            self.mineral_c_erosion.setText(self.c_locale.toString(c_erosion, 'f', 4)); self.f85_result.setText(f"C потери (эрозия) (Ф. 85): {c_erosion:.4f} т C/год (подставлено в поле выше)"); logging.info(f"AgriTab: Erosion loss calculated: {c_erosion:.4f} t C/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 85 (helper)")

    def _calculate_respiration_helper(self):
        try:
            area = get_float(self.f86_area, "Площадь (Ф.86)")
            rate = get_float(self.f86_rate, "Скорость эмиссии (Ф.86)")
            period = get_float(self.f86_period, "Вег. период (Ф.86)")
            c_resp = self.calculator.calculate_soil_respiration(area, rate, period)
            self.mineral_c_resp.setText(self.c_locale.toString(c_resp, 'f', 4))
            self.f86_result.setText(f"C потери (дыхание) (Ф. 86): {c_resp:.4f} т C/год (подставлено в поле выше)")
            logging.info(f"AgriTab: Respiration loss calculated: {c_resp:.4f} t C/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 86 (helper)")


    def _calculate_organic_co2(self):
        try:
            area = get_float(self.organic_area, "Площадь осушенных почв"); co2_emissions = self.calculator.calculate_organic_soil_co2(area)
            result = f"Выбросы CO2 от орган. почв (Ф. 87): {co2_emissions:.4f} т CO2/год"; self.f87_result.setText(result); logging.info(f"AgriTab: Organic soil CO2 calculated: {co2_emissions:.4f} t CO2/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 87")

    def _calculate_organic_n2o(self):
        try:
            area = get_float(self.organic_area, "Площадь осушенных почв"); n2o_emissions = self.calculator.calculate_organic_soil_n2o(area); gwp_n2o = 265; co2_eq = n2o_emissions * gwp_n2o
            result = (f"Выбросы N2O от орган. почв (Ф. 88): {n2o_emissions:.6f} т N2O/год\nCO2-эквивалент: {co2_eq:.4f} т CO2-экв/год"); self.f88_result.setText(result); logging.info(f"AgriTab: Organic soil N2O calculated: {n2o_emissions:.6f} t N2O/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 88")

    def _calculate_organic_ch4(self):
        try:
            area = get_float(self.organic_area, "Площадь осушенных почв"); frac_ditch = get_float(self.organic_ch4_frac_ditch, "Доля канав"); ef_land = get_float(self.organic_ch4_ef_land, "EF земли"); ef_ditch = get_float(self.organic_ch4_ef_ditch, "EF канав")
            ch4_emissions_kg = self.calculator.calculate_drained_ch4_emissions(area=area, frac_ditch=frac_ditch, ef_land=ef_land, ef_ditch=ef_ditch); ch4_emissions_tons = ch4_emissions_kg / 1000.0; gwp_ch4 = 28; co2_eq = ch4_emissions_tons * gwp_ch4
            result = (f"Выбросы CH4 от осуш. орган. почв (Ф. 75/89): {ch4_emissions_tons:.6f} т CH4/год\nCO2-эквивалент: {co2_eq:.4f} т CO2-экв/год"); self.f89_result.setText(result); logging.info(f"AgriTab: Organic soil CH4 calculated: {ch4_emissions_tons:.6f} t CH4/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 75/89")

    def _calculate_biomass_change(self):
        try:
            gain = get_float(self.biomass_gain, "Прирост C"); loss = get_float(self.biomass_loss, "Потери C"); delta_c = self.calculator.calculate_biomass_carbon_change(gain, loss)
            co2_eq = delta_c * (-44/12)
            result = (f"ΔC биомассы (Ф. 77): {delta_c:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.f77_result.setText(result); logging.info(f"AgriTab: Biomass ΔC calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 77")

    def _calculate_agricultural_fire(self):
        try:
            area = get_float(self.agri_fire_area, "Площадь пожара"); biomass = get_float(self.agri_fire_biomass, "Масса биомассы"); comb_factor = get_float(self.agri_fire_comb_factor, "Коэф. сгорания"); gas_type = self.agri_fire_gas_type.currentText()
            ef_value = self.data_service.get_fire_emission_factor('сельхоз_остатки', gas_type)
            if ef_value is None: raise ValueError(f"Коэффициент выброса для {gas_type} не найден.")
            emission = self.calculator.calculate_agricultural_fire_emissions(area=area, biomass=biomass, combustion=comb_factor, emission_factor=ef_value)
            result = (f"Выбросы от пожара (Ф. 76/90):\nПлощадь={area:.2f} га, Биомасса={biomass:.2f} т/га, К сгор.={comb_factor:.3f}\nВыбросы {gas_type}: {emission:.4f} т")
            gwp_factors = {"CO2": 1, "CH4": 28, "N2O": 265}; gwp = gwp_factors.get(gas_type, 1)
            if gwp != 1: co2_eq = emission * gwp; result += f" (CO2-экв: {co2_eq:.4f} т)"
            self.f90_result.setText(result); logging.info(f"AgriTab: Agricultural fire emission calculated: {emission:.4f} t {gas_type}")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 76/90")

    def get_summary_data(self) -> Dict[str, float]:
        """Собирает данные для сводного отчета."""
        data = {
            'absorption_c': 0.0,
            'emission_co2': 0.0,
            'emission_ch4': 0.0,
            'emission_n2o': 0.0,
            'details': ''
        }
        details = "Сельскохозяйственные земли:\n"

        try:
            # Собираем данные из Ф. 77 (изменение углерода в биомассе)
            if hasattr(self, 'biomass_gain') and self.biomass_gain.text():
                gain = float(self.biomass_gain.text().replace(',', '.'))
                loss = float(self.biomass_loss.text().replace(',', '.')) if self.biomass_loss.text() else 0.0
                net_biomass_c = gain - loss
                if net_biomass_c < 0:
                    data['absorption_c'] += abs(net_biomass_c)
                details += f"  - Изменение C в биомассе: {net_biomass_c:.2f} т C/год\n"
        except:
            details += "  - Данные биомассы не заполнены\n"

        try:
            # Собираем выбросы от органических почв (Ф. 87-89)
            if hasattr(self, 'organic_area') and self.organic_area.text():
                details += "  - Выбросы от органических почв учтены\n"
        except:
            pass

        data['details'] = details
        return data


