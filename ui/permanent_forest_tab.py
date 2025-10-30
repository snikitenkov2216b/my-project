# ui/permanent_forest_tab.py
"""
Вкладка для расчетов поглощения в постоянных лесах.
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

from calculations.absorption_permanent_forest import PermanentForestCalculator
from data_models_extended import DataService

from ui.tab_data_mixin import TabDataMixin
from ui.absorption_utils import create_line_edit, get_float, handle_error


class PermanentForestTab(TabDataMixin, QWidget):
    """Вкладка для расчетов по постоянным лесным землям (Формулы 27-59)."""
    def __init__(self, calculator: PermanentForestCalculator, data_service: DataService, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.data_service = data_service
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()
        logging.info("PermanentForestTab initialized.")

    def _init_ui(self):
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget); main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(main_widget)
        outer_layout = QVBoxLayout(self); outer_layout.addWidget(scroll_area)

        # --- Блок Биомасса (Ф. 27-35) ---
        biomass_group = QGroupBox("Расчеты по биомассе (Формулы 27-35)")
        biomass_layout = QVBoxLayout(biomass_group)

        layout_f27 = QFormLayout()
        self.f27_volume = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас древесины, м³") # м³, а не м³/га
        self.f27_conversion_factor = create_line_edit(self, validator_params=(0, 10, 4), tooltip="Коэффициент перевода KP_ij")
        layout_f27.addRow("Запас древесины (V_ij, м³):", self.f27_volume)
        layout_f27.addRow("Коэф. перевода биомассы (KP_ij):", self.f27_conversion_factor)
        calc_f27_btn = QPushButton("Рассчитать C биомассы (Ф. 27)"); calc_f27_btn.clicked.connect(self._calculate_f27)
        layout_f27.addRow(calc_f27_btn)
        self.f27_result = QLabel("—"); self.f27_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f27_result.setWordWrap(True)
        layout_f27.addRow("Результат:", self.f27_result)
        biomass_layout.addLayout(layout_f27)

        layout_f28 = QFormLayout()
        self.f28_carbon_stock = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Запас углерода, т C (из Ф.27 или др.)")
        self.f28_area = create_line_edit(self, validator_params=(0.001, 1e12, 4), tooltip="Площадь участка, га")
        layout_f28.addRow("Запас углерода (CP_ij, т C):", self.f28_carbon_stock)
        layout_f28.addRow("Площадь (S_ij, га):", self.f28_area)
        calc_f28_btn = QPushButton("Рассчитать средний C/га (Ф. 28)"); calc_f28_btn.clicked.connect(self._calculate_f28)
        layout_f28.addRow(calc_f28_btn)
        self.f28_result = QLabel("—"); self.f28_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f28_result.setWordWrap(True)
        layout_f28.addRow("Результат:", self.f28_result)
        biomass_layout.addLayout(layout_f28)

        layout_f35 = QFormLayout()
        self.f35_absorption = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Общая абсорбция углерода, т C/год (из Ф.30)")
        self.f35_harvest_loss = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери от рубок, т C/год (из Ф.33)")
        self.f35_fire_loss = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери от пожаров, т C/год (из Ф.34)")
        layout_f35.addRow("Абсорбция (AbP, т C/год):", self.f35_absorption)
        layout_f35.addRow("Потери от рубок (LsPH, т C/год):", self.f35_harvest_loss)
        layout_f35.addRow("Потери от пожаров (LsPF, т C/год):", self.f35_fire_loss)
        calc_f35_btn = QPushButton("Рассчитать бюджет биомассы (Ф. 35)"); calc_f35_btn.clicked.connect(self._calculate_f35)
        layout_f35.addRow(calc_f35_btn)
        self.f35_result = QLabel("—"); self.f35_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f35_result.setWordWrap(True)
        layout_f35.addRow("Результат:", self.f35_result)
        biomass_layout.addLayout(layout_f35)

        main_layout.addWidget(biomass_group)

        # --- Блок Мертвое органическое вещество (Ф. 36-42) ---
        deadwood_group = QGroupBox("Расчеты по мертвой древесине (Формулы 36-42)")
        deadwood_layout = QVBoxLayout(deadwood_group)
        # Пример для Ф.36
        layout_f36 = QFormLayout()
        self.f36_volume = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас древесины (живой), м³")
        self.f36_conversion_factor = create_line_edit(self, validator_params=(0, 10, 4), tooltip="Коэффициент перевода для мертвой древесины KD_ij")
        layout_f36.addRow("Запас древесины (V_ij, м³):", self.f36_volume)
        layout_f36.addRow("Коэф. перевода мертв.др. (KD_ij):", self.f36_conversion_factor)
        calc_f36_btn = QPushButton("Рассчитать C мертв. древесины (Ф. 36)"); calc_f36_btn.clicked.connect(self._calculate_f36)
        layout_f36.addRow(calc_f36_btn)
        self.f36_result = QLabel("—"); self.f36_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f36_result.setWordWrap(True)
        layout_f36.addRow("Результат:", self.f36_result)
        deadwood_layout.addLayout(layout_f36)

        # Ф. 37-42: Детальные расчеты по мертвой древесине
        layout_f37_42 = QFormLayout()
        deadwood_layout.addWidget(QLabel("Детализация по мертвой древесине (Ф. 37-42):"))

        # Ф. 37: Средний запас углерода на га
        self.f37_carbon_stock = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас углерода в мертвой древесине, т C (из Ф.36)")
        self.f37_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь, га")
        layout_f37_42.addRow("Запас C мертв.др. (CD_ij, т C):", self.f37_carbon_stock)
        layout_f37_42.addRow("Площадь (S_ij, га):", self.f37_area)
        calc_f37_btn = QPushButton("Рассчитать средний запас C (Ф. 37)"); calc_f37_btn.clicked.connect(self._calculate_f37)
        layout_f37_42.addRow(calc_f37_btn)
        self.f37_result = QLabel("—"); layout_f37_42.addRow("MCD_ij (т C/га):", self.f37_result)

        # Ф. 38-39: Скорость и общая абсорбция
        self.f38_mcd_prev = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Средний запас C пред. группы, т C/га")
        self.f38_mcd_current = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Средний запас C текущей группы, т C/га")
        self.f38_mcd_next = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Средний запас C следующей группы, т C/га")
        self.f38_ti_prev = create_line_edit(self, validator_params=(0, 200, 0), tooltip="Возрастной интервал пред. группы, лет")
        self.f38_ti_current = create_line_edit(self, validator_params=(0, 200, 0), tooltip="Возрастной интервал текущей группы, лет")
        self.f38_ti_next = create_line_edit(self, validator_params=(0, 200, 0), tooltip="Возрастной интервал след. группы, лет")
        layout_f37_42.addRow("MCD_i-1,j (т C/га):", self.f38_mcd_prev)
        layout_f37_42.addRow("MCD_ij (т C/га):", self.f38_mcd_current)
        layout_f37_42.addRow("MCD_i+1,j (т C/га):", self.f38_mcd_next)
        layout_f37_42.addRow("TI_i-1,j (лет):", self.f38_ti_prev)
        layout_f37_42.addRow("TI_ij (лет):", self.f38_ti_current)
        layout_f37_42.addRow("TI_i+1,j (лет):", self.f38_ti_next)
        calc_f38_btn = QPushButton("Рассчитать скорость абсорбции (Ф. 38)"); calc_f38_btn.clicked.connect(self._calculate_f38)
        layout_f37_42.addRow(calc_f38_btn)
        self.f38_result = QLabel("—"); layout_f37_42.addRow("MAbD_ij (т C/га/год):", self.f38_result)

        # Ф. 39: Общая абсорбция
        self.f39_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь, га")
        self.f39_absorption_rate = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Скорость абсорбции, т C/га/год (из Ф.38)")
        layout_f37_42.addRow("Площадь (S_ij, га):", self.f39_area)
        layout_f37_42.addRow("MAbD_ij (т C/га/год):", self.f39_absorption_rate)
        calc_f39_btn = QPushButton("Рассчитать общую абсорбцию (Ф. 39)"); calc_f39_btn.clicked.connect(self._calculate_f39)
        layout_f37_42.addRow(calc_f39_btn)
        self.f39_result = QLabel("—"); layout_f37_42.addRow("AbD_ij (т C/год):", self.f39_result)

        # Ф. 40-41: Потери при рубках и пожарах
        self.f40_41_harvest_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Годичная площадь рубок, га/год")
        self.f40_41_fire_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Годичная площадь пожаров, га/год")
        self.f40_41_mean_carbon = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Средний запас C мертв.др., т C")
        self.f40_41_mean_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Средняя площадь, га")
        layout_f37_42.addRow("ASH (га/год):", self.f40_41_harvest_area)
        layout_f37_42.addRow("ASF (га/год):", self.f40_41_fire_area)
        layout_f37_42.addRow("CD_m (т C):", self.f40_41_mean_carbon)
        layout_f37_42.addRow("S_m (га):", self.f40_41_mean_area)
        calc_f40_btn = QPushButton("Рассчитать потери от рубок (Ф. 40)"); calc_f40_btn.clicked.connect(self._calculate_f40)
        layout_f37_42.addRow(calc_f40_btn)
        self.f40_result = QLabel("—"); layout_f37_42.addRow("LsDH (т C/год):", self.f40_result)
        calc_f41_btn = QPushButton("Рассчитать потери от пожаров (Ф. 41)"); calc_f41_btn.clicked.connect(self._calculate_f41)
        layout_f37_42.addRow(calc_f41_btn)
        self.f41_result = QLabel("—"); layout_f37_42.addRow("LsDF (т C/год):", self.f41_result)

        # Ф. 42: Бюджет мертвой древесины
        self.f42_absorption = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Абсорбция, т C/год (из Ф.39)")
        self.f42_harvest_loss = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери от рубок, т C/год (из Ф.40)")
        self.f42_fire_loss = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери от пожаров, т C/год (из Ф.41)")
        layout_f37_42.addRow("AbD (т C/год):", self.f42_absorption)
        layout_f37_42.addRow("LsDH (т C/год):", self.f42_harvest_loss)
        layout_f37_42.addRow("LsDF (т C/год):", self.f42_fire_loss)
        calc_f42_btn = QPushButton("Рассчитать бюджет мертв.др. (Ф. 42)"); calc_f42_btn.clicked.connect(self._calculate_f42)
        layout_f37_42.addRow(calc_f42_btn)
        self.f42_result = QLabel("—"); layout_f37_42.addRow("BD (т C/год):", self.f42_result)

        deadwood_layout.addLayout(layout_f37_42)
        main_layout.addWidget(deadwood_group)

        # --- Блок Подстилка (Ф. 43-48) ---
        litter_group = QGroupBox("Расчеты по подстилке (Формулы 43-48)")
        litter_layout = QVBoxLayout(litter_group)
        # Пример для Ф.43
        layout_f43 = QFormLayout()
        self.f43_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь участка, га")
        self.f43_litter_factor = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Коэффициент углерода в подстилке, т C/га")
        layout_f43.addRow("Площадь (S_ij, га):", self.f43_area)
        layout_f43.addRow("Коэф. C подстилки (KL_ij, т C/га):", self.f43_litter_factor)
        calc_f43_btn = QPushButton("Рассчитать C подстилки (Ф. 43)"); calc_f43_btn.clicked.connect(self._calculate_f43)
        layout_f43.addRow(calc_f43_btn)
        self.f43_result = QLabel("—"); self.f43_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f43_result.setWordWrap(True)
        layout_f43.addRow("Результат:", self.f43_result)
        litter_layout.addLayout(layout_f43)

        # Ф. 44-48: Детальные расчеты по подстилке
        layout_f44_48 = QFormLayout()
        litter_layout.addWidget(QLabel("Детализация по подстилке (Ф. 44-48):"))

        # Ф. 44-45: Скорость и общая абсорбция подстилки
        self.f44_mcl_prev = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Средний запас C пред. группы, т C/га")
        self.f44_mcl_current = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Средний запас C текущей группы, т C/га")
        self.f44_mcl_next = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Средний запас C следующей группы, т C/га")
        self.f44_ti_prev = create_line_edit(self, validator_params=(0, 200, 0), tooltip="Возрастной интервал пред. группы, лет")
        self.f44_ti_current = create_line_edit(self, validator_params=(0, 200, 0), tooltip="Возрастной интервал текущей группы, лет")
        self.f44_ti_next = create_line_edit(self, validator_params=(0, 200, 0), tooltip="Возрастной интервал след. группы, лет")
        layout_f44_48.addRow("MCL_i-1,j (т C/га):", self.f44_mcl_prev)
        layout_f44_48.addRow("MCL_ij (т C/га):", self.f44_mcl_current)
        layout_f44_48.addRow("MCL_i+1,j (т C/га):", self.f44_mcl_next)
        layout_f44_48.addRow("TI_i-1,j (лет):", self.f44_ti_prev)
        layout_f44_48.addRow("TI_ij (лет):", self.f44_ti_current)
        layout_f44_48.addRow("TI_i+1,j (лет):", self.f44_ti_next)
        calc_f44_btn = QPushButton("Рассчитать скорость абсорбции (Ф. 44)"); calc_f44_btn.clicked.connect(self._calculate_f44)
        layout_f44_48.addRow(calc_f44_btn)
        self.f44_result = QLabel("—"); layout_f44_48.addRow("MAbL_ij (т C/га/год):", self.f44_result)

        # Ф. 45: Общая абсорбция подстилки
        self.f45_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь, га")
        self.f45_absorption_rate = create_line_edit(self, validator_params=(-100, 100, 4), tooltip="Скорость абсорбции, т C/га/год (из Ф.44)")
        layout_f44_48.addRow("Площадь (S_ij, га):", self.f45_area)
        layout_f44_48.addRow("MAbL_ij (т C/га/год):", self.f45_absorption_rate)
        calc_f45_btn = QPushButton("Рассчитать общую абсорбцию (Ф. 45)"); calc_f45_btn.clicked.connect(self._calculate_f45)
        layout_f44_48.addRow(calc_f45_btn)
        self.f45_result = QLabel("—"); layout_f44_48.addRow("AbL_ij (т C/год):", self.f45_result)

        # Ф. 46-47: Потери подстилки при рубках и пожарах
        self.f46_47_harvest_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Годичная площадь рубок, га/год")
        self.f46_47_fire_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Годичная площадь пожаров, га/год")
        self.f46_47_mean_carbon = create_line_edit(self, validator_params=(0, 1e6, 4), tooltip="Средний запас C подстилки, т C")
        self.f46_47_mean_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Средняя площадь, га")
        self.f46_47_initial_carbon = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Начальный запас C подстилки, т C/га")
        layout_f44_48.addRow("ASH (га/год):", self.f46_47_harvest_area)
        layout_f44_48.addRow("ASF (га/год):", self.f46_47_fire_area)
        layout_f44_48.addRow("CL_m (т C):", self.f46_47_mean_carbon)
        layout_f44_48.addRow("S_m (га):", self.f46_47_mean_area)
        layout_f44_48.addRow("MCL_0m (т C/га):", self.f46_47_initial_carbon)
        calc_f46_btn = QPushButton("Рассчитать потери от рубок (Ф. 46)"); calc_f46_btn.clicked.connect(self._calculate_f46)
        layout_f44_48.addRow(calc_f46_btn)
        self.f46_result = QLabel("—"); layout_f44_48.addRow("LsLH (т C/год):", self.f46_result)
        calc_f47_btn = QPushButton("Рассчитать потери от пожаров (Ф. 47)"); calc_f47_btn.clicked.connect(self._calculate_f47)
        layout_f44_48.addRow(calc_f47_btn)
        self.f47_result = QLabel("—"); layout_f44_48.addRow("LsLF (т C/год):", self.f47_result)

        # Ф. 48: Бюджет подстилки
        self.f48_absorption = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Абсорбция, т C/год (из Ф.45)")
        self.f48_harvest_loss = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери от рубок, т C/год (из Ф.46)")
        self.f48_fire_loss = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери от пожаров, т C/год (из Ф.47)")
        layout_f44_48.addRow("AbL (т C/год):", self.f48_absorption)
        layout_f44_48.addRow("LsLH (т C/год):", self.f48_harvest_loss)
        layout_f44_48.addRow("LsLF (т C/год):", self.f48_fire_loss)
        calc_f48_btn = QPushButton("Рассчитать бюджет подстилки (Ф. 48)"); calc_f48_btn.clicked.connect(self._calculate_f48)
        layout_f44_48.addRow(calc_f48_btn)
        self.f48_result = QLabel("—"); layout_f44_48.addRow("BP (т C/год):", self.f48_result)

        litter_layout.addLayout(layout_f44_48)
        main_layout.addWidget(litter_group)

        # --- Блок Почва (Ф. 49-54) ---
        soil_group = QGroupBox("Расчеты по почве (Формулы 49-54)")
        soil_layout = QVBoxLayout(soil_group)
        # Пример для Ф.49
        layout_f49 = QFormLayout()
        self.f49_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь участка, га")
        self.f49_soil_factor = create_line_edit(self, validator_params=(0, 500, 4), tooltip="Коэффициент углерода в почве, т C/га")
        layout_f49.addRow("Площадь (S_ij, га):", self.f49_area)
        layout_f49.addRow("Коэф. C почвы (KS_ij, т C/га):", self.f49_soil_factor)
        calc_f49_btn = QPushButton("Рассчитать C почвы (Ф. 49)"); calc_f49_btn.clicked.connect(self._calculate_f49)
        layout_f49.addRow(calc_f49_btn)
        self.f49_result = QLabel("—"); self.f49_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f49_result.setWordWrap(True)
        layout_f49.addRow("Результат:", self.f49_result)
        soil_layout.addLayout(layout_f49)

        # Ф. 50-54: Детальные расчеты по почве
        layout_f50_54 = QFormLayout()
        soil_layout.addWidget(QLabel("Детализация по почве (Ф. 50-54):"))

        # Ф. 50-51: Скорость и общая абсорбция почвы
        self.f50_mcs_prev = create_line_edit(self, validator_params=(0, 500, 4), tooltip="Средний запас C пред. группы, т C/га")
        self.f50_mcs_current = create_line_edit(self, validator_params=(0, 500, 4), tooltip="Средний запас C текущей группы, т C/га")
        self.f50_mcs_next = create_line_edit(self, validator_params=(0, 500, 4), tooltip="Средний запас C следующей группы, т C/га")
        self.f50_ti_prev = create_line_edit(self, validator_params=(0, 200, 0), tooltip="Возрастной интервал пред. группы, лет")
        self.f50_ti_current = create_line_edit(self, validator_params=(0, 200, 0), tooltip="Возрастной интервал текущей группы, лет")
        self.f50_ti_next = create_line_edit(self, validator_params=(0, 200, 0), tooltip="Возрастной интервал след. группы, лет")
        layout_f50_54.addRow("MCS_i-1,j (т C/га):", self.f50_mcs_prev)
        layout_f50_54.addRow("MCS_ij (т C/га):", self.f50_mcs_current)
        layout_f50_54.addRow("MCS_i+1,j (т C/га):", self.f50_mcs_next)
        layout_f50_54.addRow("TI_i-1,j (лет):", self.f50_ti_prev)
        layout_f50_54.addRow("TI_ij (лет):", self.f50_ti_current)
        layout_f50_54.addRow("TI_i+1,j (лет):", self.f50_ti_next)
        calc_f50_btn = QPushButton("Рассчитать скорость абсорбции почвой (Ф. 50)"); calc_f50_btn.clicked.connect(self._calculate_f50)
        layout_f50_54.addRow(calc_f50_btn)
        self.f50_result = QLabel("—"); layout_f50_54.addRow("MAbS_ij (т C/га/год):", self.f50_result)

        # Ф. 51: Общая абсорбция почвы
        self.f51_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь, га")
        self.f51_absorption_rate = create_line_edit(self, validator_params=(-500, 500, 4), tooltip="Скорость абсорбции, т C/га/год (из Ф.50)")
        layout_f50_54.addRow("Площадь (S_ij, га):", self.f51_area)
        layout_f50_54.addRow("MAbS_ij (т C/га/год):", self.f51_absorption_rate)
        calc_f51_btn = QPushButton("Рассчитать общую абсорбцию почвой (Ф. 51)"); calc_f51_btn.clicked.connect(self._calculate_f51)
        layout_f50_54.addRow(calc_f51_btn)
        self.f51_result = QLabel("—"); layout_f50_54.addRow("AbL_ij (т C/год):", self.f51_result)

        # Ф. 52-53: Потери углерода почвы при рубках и пожарах
        self.f52_53_harvest_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Годичная площадь рубок, га/год")
        self.f52_53_fire_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Годичная площадь пожаров, га/год")
        self.f52_53_mean_carbon = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Средний запас C почвы, т C")
        self.f52_53_mean_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Средняя площадь, га")
        self.f52_53_initial_carbon = create_line_edit(self, validator_params=(0, 500, 4), tooltip="Начальный запас C почвы, т C/га")
        layout_f50_54.addRow("ASH (га/год):", self.f52_53_harvest_area)
        layout_f50_54.addRow("ASF (га/год):", self.f52_53_fire_area)
        layout_f50_54.addRow("CS_m (т C):", self.f52_53_mean_carbon)
        layout_f50_54.addRow("S_m (га):", self.f52_53_mean_area)
        layout_f50_54.addRow("MCS_0m (т C/га):", self.f52_53_initial_carbon)
        calc_f52_btn = QPushButton("Рассчитать потери почвы от рубок (Ф. 52)"); calc_f52_btn.clicked.connect(self._calculate_f52)
        layout_f50_54.addRow(calc_f52_btn)
        self.f52_result = QLabel("—"); layout_f50_54.addRow("LsSH (т C/год):", self.f52_result)
        calc_f53_btn = QPushButton("Рассчитать потери почвы от пожаров (Ф. 53)"); calc_f53_btn.clicked.connect(self._calculate_f53)
        layout_f50_54.addRow(calc_f53_btn)
        self.f53_result = QLabel("—"); layout_f50_54.addRow("LsSF (т C/год):", self.f53_result)

        # Ф. 54: Бюджет почвы
        self.f54_absorption = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Абсорбция, т C/год (из Ф.51)")
        self.f54_harvest_loss = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери от рубок, т C/год (из Ф.52)")
        self.f54_fire_loss = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Потери от пожаров, т C/год (из Ф.53)")
        layout_f50_54.addRow("AbS (т C/год):", self.f54_absorption)
        layout_f50_54.addRow("LsSH (т C/год):", self.f54_harvest_loss)
        layout_f50_54.addRow("LsSF (т C/год):", self.f54_fire_loss)
        calc_f54_btn = QPushButton("Рассчитать бюджет почвы (Ф. 54)"); calc_f54_btn.clicked.connect(self._calculate_f54)
        layout_f50_54.addRow(calc_f54_btn)
        self.f54_result = QLabel("—"); layout_f50_54.addRow("BS (т C/год):", self.f54_result)

        soil_layout.addLayout(layout_f50_54)
        main_layout.addWidget(soil_group)

        # --- Блок Суммарный бюджет (Ф. 55) ---
        total_budget_group = QGroupBox("Суммарный бюджет углерода (Формула 55)")
        layout_f55 = QFormLayout(total_budget_group)
        self.f55_biomass_budget = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Бюджет биомассы, т C/год (из Ф.35)")
        self.f55_deadwood_budget = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Бюджет мертвой древесины, т C/год (из Ф.42)")
        self.f55_litter_budget = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Бюджет подстилки, т C/год (из Ф.48)")
        self.f55_soil_budget = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Бюджет почвы, т C/год (из Ф.54)")
        layout_f55.addRow("Бюджет биомассы (BP, т C/год):", self.f55_biomass_budget)
        layout_f55.addRow("Бюджет мертв.древ. (BD, т C/год):", self.f55_deadwood_budget)
        layout_f55.addRow("Бюджет подстилки (BL, т C/год):", self.f55_litter_budget)
        layout_f55.addRow("Бюджет почвы (BS, т C/год):", self.f55_soil_budget)
        calc_f55_btn = QPushButton("Рассчитать суммарный бюджет (Ф. 55)"); calc_f55_btn.clicked.connect(self._calculate_f55)
        layout_f55.addRow(calc_f55_btn)
        self.f55_result = QLabel("—"); self.f55_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f55_result.setWordWrap(True)
        layout_f55.addRow("Результат:", self.f55_result)
        main_layout.addWidget(total_budget_group)

        # --- Блок Выбросы от осушения и пожаров (Ф. 56-59) ---
        emissions_group = QGroupBox("Выбросы CO2, N2O, CH4 (Формулы 56-59)")
        emissions_layout = QVBoxLayout(emissions_group)

        layout_f56_58 = QFormLayout()
        self.f56_58_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь осушенных лесных почв, га")
        layout_f56_58.addRow("Площадь осушения (A, га):", self.f56_58_area)
        # Ф.56 CO2
        self.f56_ef = create_line_edit(self, "0.71", (0, 100, 4), tooltip="Коэф. выброса CO2, т C/га/год")
        layout_f56_58.addRow("EF CO2 (т C/га/год):", self.f56_ef)
        calc_f56_btn = QPushButton("Рассчитать CO2 от осушения (Ф. 56)"); calc_f56_btn.clicked.connect(self._calculate_f56)
        layout_f56_58.addRow(calc_f56_btn)
        self.f56_result = QLabel("—"); self.f56_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f56_result.setWordWrap(True)
        layout_f56_58.addRow("Результат Ф.56:", self.f56_result)
        # Ф.57 N2O
        self.f57_ef = create_line_edit(self, "1.71", (0, 100, 4), tooltip="Коэф. выброса N2O, кг N/га/год")
        layout_f56_58.addRow("EF N2O (кг N/га/год):", self.f57_ef)
        calc_f57_btn = QPushButton("Рассчитать N2O от осушения (Ф. 57)"); calc_f57_btn.clicked.connect(self._calculate_f57)
        layout_f56_58.addRow(calc_f57_btn)
        self.f57_result = QLabel("—"); self.f57_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f57_result.setWordWrap(True)
        layout_f56_58.addRow("Результат Ф.57:", self.f57_result)
        # Ф.58 CH4
        self.f58_frac_ditch = create_line_edit(self, "0.025", (0, 1, 3), tooltip="Доля канав")
        self.f58_ef_land = create_line_edit(self, "4.5", (0, 1e6, 4), tooltip="EF земли, кг CH4/га/год")
        self.f58_ef_ditch = create_line_edit(self, "217", (0, 1e6, 4), tooltip="EF канав, кг CH4/га/год")
        layout_f56_58.addRow("Доля канав (Frac_ditch):", self.f58_frac_ditch)
        layout_f56_58.addRow("EF_land CH4 (кг/га/год):", self.f58_ef_land)
        layout_f56_58.addRow("EF_ditch CH4 (кг/га/год):", self.f58_ef_ditch)
        calc_f58_btn = QPushButton("Рассчитать CH4 от осушения (Ф. 58)"); calc_f58_btn.clicked.connect(self._calculate_f58)
        layout_f56_58.addRow(calc_f58_btn)
        self.f58_result = QLabel("—"); self.f58_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f58_result.setWordWrap(True)
        layout_f56_58.addRow("Результат Ф.58:", self.f58_result)
        emissions_layout.addLayout(layout_f56_58)

        fire_layout = QFormLayout()
        self.f59_area = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Площадь лесного пожара, га")
        self.f59_fuel_mass = create_line_edit(self, validator_params=(0, 1000, 4), tooltip="Масса топлива, т/га")
        self.f59_comb_factor = create_line_edit(self, validator_params=(0.01, 1.0, 3), tooltip="Коэффициент сгорания (доля)")
        self.f59_gas_type = QComboBox(); self.f59_gas_type.addItems(["CO2", "CH4", "N2O"])
        fire_layout.addRow("Площадь пожара (A, га):", self.f59_area)
        fire_layout.addRow("Масса топлива (MB, т/га):", self.f59_fuel_mass)
        fire_layout.addRow("Коэф. сгорания (C_f, доля):", self.f59_comb_factor)
        fire_layout.addRow("Тип газа:", self.f59_gas_type)
        calc_f59_btn = QPushButton("Рассчитать выброс от пожара (Ф. 59)"); calc_f59_btn.clicked.connect(self._calculate_f59)
        fire_layout.addRow(calc_f59_btn)
        self.f59_result = QLabel("—"); self.f59_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;"); self.f59_result.setWordWrap(True)
        fire_layout.addRow("Результат:", self.f59_result)
        emissions_layout.addLayout(fire_layout)

        main_layout.addWidget(emissions_group)


    # --- Методы расчета для PermanentForestTab ---
    def _calculate_f27(self):
        try:
            volume = get_float(self.f27_volume, "Запас древесины (Ф.27)")
            factor = get_float(self.f27_conversion_factor, "Коэф. перевода (Ф.27)")
            carbon_stock = self.calculator.calculate_biomass_carbon_stock(volume, factor)
            self.f27_result.setText(f"Запас углерода в биомассе: {carbon_stock:.4f} т C")
            logging.info(f"PermanentForestTab: F27 calculated: {carbon_stock:.4f} t C")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 27")

    def _calculate_f28(self):
        try:
            carbon_stock = get_float(self.f28_carbon_stock, "Запас углерода (Ф.28)")
            area = get_float(self.f28_area, "Площадь (Ф.28)")
            mean_carbon = self.calculator.calculate_mean_carbon_per_hectare(carbon_stock, area)
            self.f28_result.setText(f"Средний C/га: {mean_carbon:.4f} т C/га")
            logging.info(f"PermanentForestTab: F28 calculated: {mean_carbon:.4f} t C/ha")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 28")

    def _calculate_f35(self):
        try:
            absorption = get_float(self.f35_absorption, "Абсорбция (Ф.35)")
            harvest_loss = get_float(self.f35_harvest_loss, "Потери от рубок (Ф.35)")
            fire_loss = get_float(self.f35_fire_loss, "Потери от пожаров (Ф.35)")
            budget = self.calculator.calculate_biomass_budget(absorption, harvest_loss, fire_loss)
            co2_eq = budget * (-44/12)
            result = (f"Бюджет биомассы (Ф. 35): {budget:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.f35_result.setText(result); logging.info(f"PermanentForestTab: F35 calculated: {budget:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 35")

    def _calculate_f36(self):
        try:
            volume = get_float(self.f36_volume, "Запас древесины (Ф.36)")
            factor = get_float(self.f36_conversion_factor, "Коэф. перевода мертв.др. (Ф.36)")
            carbon_stock = self.calculator.calculate_deadwood_carbon_stock(volume, factor)
            self.f36_result.setText(f"C мертвой древесины: {carbon_stock:.4f} т C")
            logging.info(f"PermanentForestTab: F36 calculated: {carbon_stock:.4f} t C")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 36")

    def _calculate_f37(self):
        try:
            carbon_stock = get_float(self.f37_carbon_stock, "Запас C мертв.др. (Ф.37)")
            area = get_float(self.f37_area, "Площадь (Ф.37)")
            mean_carbon = self.calculator.calculate_mean_deadwood_carbon_per_hectare(carbon_stock, area)
            self.f37_result.setText(f"{mean_carbon:.4f}")
            logging.info(f"PermanentForestTab: F37 calculated: {mean_carbon:.4f} t C/ha")
        except Exception as e:
            handle_error(self, e, "PermanentForestTab", "Ф. 37")

    def _calculate_f38(self):
        try:
            mcd_prev = get_float(self.f38_mcd_prev, "MCD_i-1,j (Ф.38)")
            mcd_current = get_float(self.f38_mcd_current, "MCD_ij (Ф.38)")
            mcd_next = get_float(self.f38_mcd_next, "MCD_i+1,j (Ф.38)")
            ti_prev = get_float(self.f38_ti_prev, "TI_i-1,j (Ф.38)")
            ti_current = get_float(self.f38_ti_current, "TI_ij (Ф.38)")
            ti_next = get_float(self.f38_ti_next, "TI_i+1,j (Ф.38)")
            absorption_rate = self.calculator.calculate_deadwood_absorption_rate(
                mcd_current, mcd_prev, mcd_next, ti_prev, ti_current, ti_next
            )
            self.f38_result.setText(f"{absorption_rate:.4f}")
            logging.info(f"PermanentForestTab: F38 calculated: {absorption_rate:.4f} t C/ha/year")
        except Exception as e:
            handle_error(self, e, "PermanentForestTab", "Ф. 38")

    def _calculate_f39(self):
        try:
            area = get_float(self.f39_area, "Площадь (Ф.39)")
            absorption_rate = get_float(self.f39_absorption_rate, "MAbD_ij (Ф.39)")
            total_absorption = self.calculator.calculate_deadwood_total_absorption(area, absorption_rate)
            self.f39_result.setText(f"{total_absorption:.4f}")
            logging.info(f"PermanentForestTab: F39 calculated: {total_absorption:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 39")

    def _calculate_f40(self):
        try:
            harvest_area = get_float(self.f40_41_harvest_area, "ASH (Ф.40)")
            mean_carbon = get_float(self.f40_41_mean_carbon, "CD_m (Ф.40)")
            mean_area = get_float(self.f40_41_mean_area, "S_m (Ф.40)")
            harvest_loss = self.calculator.calculate_deadwood_harvest_loss(harvest_area, mean_carbon, mean_area)
            self.f40_result.setText(f"{harvest_loss:.4f}")
            logging.info(f"PermanentForestTab: F40 calculated: {harvest_loss:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 40")

    def _calculate_f41(self):
        try:
            fire_area = get_float(self.f40_41_fire_area, "ASF (Ф.41)")
            mean_carbon = get_float(self.f40_41_mean_carbon, "CD_a (Ф.41)")
            mean_area = get_float(self.f40_41_mean_area, "S_a (Ф.41)")
            fire_loss = self.calculator.calculate_deadwood_fire_loss(fire_area, mean_carbon, mean_area)
            self.f41_result.setText(f"{fire_loss:.4f}")
            logging.info(f"PermanentForestTab: F41 calculated: {fire_loss:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 41")

    def _calculate_f42(self):
        try:
            absorption = get_float(self.f42_absorption, "AbD (Ф.42)")
            harvest_loss = get_float(self.f42_harvest_loss, "LsDH (Ф.42)")
            fire_loss = get_float(self.f42_fire_loss, "LsDF (Ф.42)")
            budget = self.calculator.calculate_deadwood_budget(absorption, harvest_loss, fire_loss)
            self.f42_result.setText(f"{budget:.4f}")
            logging.info(f"PermanentForestTab: F42 calculated: {budget:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 42")

    def _calculate_f43(self):
        try:
            area = get_float(self.f43_area, "Площадь (Ф.43)")
            factor = get_float(self.f43_litter_factor, "Коэф. C подстилки (Ф.43)")
            carbon_stock = self.calculator.calculate_litter_carbon_stock(area, factor)
            self.f43_result.setText(f"C подстилки: {carbon_stock:.4f} т C")
            logging.info(f"PermanentForestTab: F43 calculated: {carbon_stock:.4f} t C")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 43")

    def _calculate_f44(self):
        try:
            mcl_prev = get_float(self.f44_mcl_prev, "MCL_i-1,j (Ф.44)")
            mcl_current = get_float(self.f44_mcl_current, "MCL_ij (Ф.44)")
            mcl_next = get_float(self.f44_mcl_next, "MCL_i+1,j (Ф.44)")
            ti_prev = get_float(self.f44_ti_prev, "TI_i-1,j (Ф.44)")
            ti_current = get_float(self.f44_ti_current, "TI_ij (Ф.44)")
            ti_next = get_float(self.f44_ti_next, "TI_i+1,j (Ф.44)")
            absorption_rate = self.calculator.calculate_litter_absorption_rate(
                mcl_current, mcl_prev, mcl_next, ti_prev, ti_current, ti_next
            )
            self.f44_result.setText(f"{absorption_rate:.4f}")
            logging.info(f"PermanentForestTab: F44 calculated: {absorption_rate:.4f} t C/ha/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 44")

    def _calculate_f45(self):
        try:
            area = get_float(self.f45_area, "Площадь (Ф.45)")
            absorption_rate = get_float(self.f45_absorption_rate, "MAbL_ij (Ф.45)")
            total_absorption = self.calculator.calculate_litter_total_absorption(area, absorption_rate)
            self.f45_result.setText(f"{total_absorption:.4f}")
            logging.info(f"PermanentForestTab: F45 calculated: {total_absorption:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 45")

    def _calculate_f46(self):
        try:
            harvest_area = get_float(self.f46_47_harvest_area, "ASH (Ф.46)")
            mean_carbon = get_float(self.f46_47_mean_carbon, "CL_m (Ф.46)")
            mean_area = get_float(self.f46_47_mean_area, "S_m (Ф.46)")
            initial_carbon = get_float(self.f46_47_initial_carbon, "MCL_0m (Ф.46)")
            harvest_loss = self.calculator.calculate_litter_harvest_loss(
                harvest_area, mean_carbon, mean_area, initial_carbon
            )
            self.f46_result.setText(f"{harvest_loss:.4f}")
            logging.info(f"PermanentForestTab: F46 calculated: {harvest_loss:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 46")

    def _calculate_f47(self):
        try:
            fire_area = get_float(self.f46_47_fire_area, "ASF (Ф.47)")
            mean_carbon = get_float(self.f46_47_mean_carbon, "CL_a (Ф.47)")
            mean_area = get_float(self.f46_47_mean_area, "S_a (Ф.47)")
            initial_carbon = get_float(self.f46_47_initial_carbon, "MCL_0a (Ф.47)")
            fire_loss = self.calculator.calculate_litter_fire_loss(
                fire_area, mean_carbon, mean_area, initial_carbon
            )
            self.f47_result.setText(f"{fire_loss:.4f}")
            logging.info(f"PermanentForestTab: F47 calculated: {fire_loss:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 47")

    def _calculate_f48(self):
        try:
            absorption = get_float(self.f48_absorption, "AbL (Ф.48)")
            harvest_loss = get_float(self.f48_harvest_loss, "LsLH (Ф.48)")
            fire_loss = get_float(self.f48_fire_loss, "LsLF (Ф.48)")
            budget = self.calculator.calculate_litter_budget(absorption, harvest_loss, fire_loss)
            self.f48_result.setText(f"{budget:.4f}")
            logging.info(f"PermanentForestTab: F48 calculated: {budget:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 48")

    def _calculate_f49(self):
        try:
            area = get_float(self.f49_area, "Площадь (Ф.49)")
            factor = get_float(self.f49_soil_factor, "Коэф. C почвы (Ф.49)")
            carbon_stock = self.calculator.calculate_soil_carbon_stock(area, factor)
            self.f49_result.setText(f"C почвы: {carbon_stock:.4f} т C")
            logging.info(f"PermanentForestTab: F49 calculated: {carbon_stock:.4f} t C")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 49")

    def _calculate_f50(self):
        try:
            mcs_prev = get_float(self.f50_mcs_prev, "MCS_i-1,j (Ф.50)")
            mcs_current = get_float(self.f50_mcs_current, "MCS_ij (Ф.50)")
            mcs_next = get_float(self.f50_mcs_next, "MCS_i+1,j (Ф.50)")
            ti_prev = get_float(self.f50_ti_prev, "TI_i-1,j (Ф.50)")
            ti_current = get_float(self.f50_ti_current, "TI_ij (Ф.50)")
            ti_next = get_float(self.f50_ti_next, "TI_i+1,j (Ф.50)")
            absorption_rate = self.calculator.calculate_soil_absorption(
                mcs_current, mcs_prev, mcs_next, ti_prev, ti_current, ti_next
            )
            self.f50_result.setText(f"{absorption_rate:.4f}")
            logging.info(f"PermanentForestTab: F50 calculated: {absorption_rate:.4f} t C/ha/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 50")

    def _calculate_f51(self):
        try:
            area = get_float(self.f51_area, "Площадь (Ф.51)")
            absorption_rate = get_float(self.f51_absorption_rate, "MAbS_ij (Ф.51)")
            total_absorption = self.calculator.calculate_soil_total_absorption(area, absorption_rate)
            self.f51_result.setText(f"{total_absorption:.4f}")
            logging.info(f"PermanentForestTab: F51 calculated: {total_absorption:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 51")

    def _calculate_f52(self):
        try:
            harvest_area = get_float(self.f52_53_harvest_area, "ASH (Ф.52)")
            mean_carbon = get_float(self.f52_53_mean_carbon, "CS_m (Ф.52)")
            mean_area = get_float(self.f52_53_mean_area, "S_m (Ф.52)")
            initial_carbon = get_float(self.f52_53_initial_carbon, "MCS_0m (Ф.52)")
            harvest_loss = self.calculator.calculate_soil_harvest_loss(
                harvest_area, mean_carbon, mean_area, initial_carbon
            )
            self.f52_result.setText(f"{harvest_loss:.4f}")
            logging.info(f"PermanentForestTab: F52 calculated: {harvest_loss:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 52")

    def _calculate_f53(self):
        try:
            fire_area = get_float(self.f52_53_fire_area, "ASF (Ф.53)")
            mean_carbon = get_float(self.f52_53_mean_carbon, "CS_a (Ф.53)")
            mean_area = get_float(self.f52_53_mean_area, "S_a (Ф.53)")
            initial_carbon = get_float(self.f52_53_initial_carbon, "MCS_0a (Ф.53)")
            fire_loss = self.calculator.calculate_soil_fire_loss(
                fire_area, mean_carbon, mean_area, initial_carbon
            )
            self.f53_result.setText(f"{fire_loss:.4f}")
            logging.info(f"PermanentForestTab: F53 calculated: {fire_loss:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 53")

    def _calculate_f54(self):
        try:
            absorption = get_float(self.f54_absorption, "AbS (Ф.54)")
            harvest_loss = get_float(self.f54_harvest_loss, "LsSH (Ф.54)")
            fire_loss = get_float(self.f54_fire_loss, "LsSF (Ф.54)")
            budget = self.calculator.calculate_soil_budget(absorption, harvest_loss, fire_loss)
            self.f54_result.setText(f"{budget:.4f}")
            logging.info(f"PermanentForestTab: F54 calculated: {budget:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 54")

    def _calculate_f55(self):
        try:
            bp = get_float(self.f55_biomass_budget, "Бюджет биомассы (Ф.55)")
            # !!! ВАЖНО: Нужны результаты расчетов Ф.42, Ф.48, Ф.54 для BD, BL, BS
            # Заглушки, пока нет UI для них:
            bd = get_float(self.f55_deadwood_budget, "Бюджет мертв.древ. (Ф.55)") # Заглушка
            bl = get_float(self.f55_litter_budget, "Бюджет подстилки (Ф.55)")    # Заглушка
            bs = get_float(self.f55_soil_budget, "Бюджет почвы (Ф.55)")         # Заглушка
            # bd = self._calculate_f42() # Примерно так должно быть
            # bl = self._calculate_f48()
            # bs = self._calculate_f54()
            total_budget = self.calculator.calculate_total_budget(bp, bd, bl, bs)
            co2_eq = total_budget * (-44/12)
            result = (f"Суммарный бюджет (Ф. 55):\n"
                      f"BT = {total_budget:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год\n"
                      f"({ 'Поглощение CO2' if co2_eq < 0 else 'Выброс CO2'})")
            self.f55_result.setText(result); logging.info(f"PermanentForestTab: F55 calculated: {total_budget:.4f} t C/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 55")

    def _calculate_f56(self):
        try:
            area = get_float(self.f56_58_area, "Площадь осушения (Ф.56)")
            ef = get_float(self.f56_ef, "Коэф. выброса (Ф.56)")
            co2_emission = self.calculator.calculate_drained_forest_co2(area, ef)
            self.f56_result.setText(f"CO2 от осушения: {co2_emission:.4f} т CO2/год")
            logging.info(f"PermanentForestTab: F56 calculated: {co2_emission:.4f} t CO2/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 56")

    def _calculate_f57(self):
        try:
            area = get_float(self.f56_58_area, "Площадь осушения (Ф.57)")
            ef = get_float(self.f57_ef, "Коэф. выброса N2O (Ф.57)")
            n2o_emission = self.calculator.calculate_drained_forest_n2o(area, ef)
            co2_eq = n2o_emission * 265
            self.f57_result.setText(f"N2O от осушения: {n2o_emission:.6f} т N2O/год\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"PermanentForestTab: F57 calculated: {n2o_emission:.6f} t N2O/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 57")

    def _calculate_f58(self):
        try:
            area = get_float(self.f56_58_area, "Площадь осушения (Ф.58)")
            frac_ditch = get_float(self.f58_frac_ditch, "Доля канав (Ф.58)")
            ef_land = get_float(self.f58_ef_land, "EF_land CH4 (Ф.58)")
            ef_ditch = get_float(self.f58_ef_ditch, "EF_ditch CH4 (Ф.58)")
            ch4_emission_kg = self.calculator.calculate_drained_forest_ch4(area, frac_ditch, ef_land, ef_ditch)
            ch4_emission_t = ch4_emission_kg / 1000.0
            co2_eq = ch4_emission_t * 28
            self.f58_result.setText(f"CH4 от осушения: {ch4_emission_t:.6f} т CH4/год ({ch4_emission_kg:.3f} кг/год)\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"PermanentForestTab: F58 calculated: {ch4_emission_t:.6f} t CH4/year")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 58")

    def _calculate_f59(self):
        try:
            area = get_float(self.f59_area, "Площадь пожара (Ф.59)")
            fuel_mass = get_float(self.f59_fuel_mass, "Масса топлива (Ф.59)")
            comb_factor = get_float(self.f59_comb_factor, "Коэф. сгорания (Ф.59)")
            gas_type = self.f59_gas_type.currentText()
            ef_value = self.data_service.get_fire_emission_factor('леса', gas_type)
            if ef_value is None: raise ValueError(f"Коэффициент выброса для {gas_type} (леса) не найден.")
            emission = self.calculator.calculate_forest_fire_emissions(area, fuel_mass, comb_factor, ef_value)
            result = f"Выбросы от пожара (Ф. 59) {gas_type}: {emission:.4f} т"
            gwp_factors = {"CO2": 1, "CH4": 28, "N2O": 265}
            gwp = gwp_factors.get(gas_type, 1)
            if gwp != 1: co2_eq = emission * gwp; result += f" (CO2-экв: {co2_eq:.4f} т)"
            self.f59_result.setText(result); logging.info(f"PermanentForestTab: F59 calculated: {emission:.4f} t {gas_type}")
        except Exception as e:

            handle_error(self, e, "PermanentForestTab", "Ф. 59")

    def get_summary_data(self) -> Dict[str, float]:
        """Собирает данные для сводного отчета."""
        data = {
            'absorption_c': 0.0,
            'emission_co2': 0.0,
            'emission_ch4': 0.0,
            'emission_n2o': 0.0,
            'details': ''
        }
        details = "Постоянные лесные земли:\n"

        try:
            # Собираем данные из Ф. 27 (запас углерода в биомассе)
            if hasattr(self, 'f27_area') and self.f27_area.text() and self.f27_carbon_factor.text():
                area = float(self.f27_area.text().replace(',', '.'))
                c_factor = float(self.f27_carbon_factor.text().replace(',', '.'))
                c_stock = area * c_factor
                details += f"  - Запас C в биомассе: {c_stock:.2f} т C\n"
        except:
            details += "  - Данные Ф. 27 не заполнены\n"

        try:
            # Собираем выбросы от осушенных лесов (Ф. 56-58)
            if hasattr(self, 'f56_58_area') and self.f56_58_area.text():
                details += "  - Выбросы от осушенных лесов учтены\n"
        except:
            pass

        data['details'] = details
        return data


