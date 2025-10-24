# ui/absorption_tabs.py
"""
UI вкладки для расчетов поглощения парниковых газов.
Полная реализация интерфейса для всех формул поглощения.
"""
import logging
import math
from typing import List, Dict, Tuple # Добавлен typing для подсказок
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QGroupBox,
    QTextEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QSpinBox, QDoubleSpinBox, QMessageBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt, QLocale

# Импортируем соответствующие калькуляторы
from calculations.absorption_forest_restoration import (
    ForestRestorationCalculator, ForestInventoryData, LandReclamationCalculator
)
from calculations.absorption_agricultural import (
    AgriculturalLandCalculator, LandConversionCalculator, CropData, LivestockData
)
from calculations.absorption_permanent_forest import (
    PermanentForestCalculator, ProtectiveForestCalculator
)

# Добавляем импорт ExtendedDataService и ExtendedCalculatorFactory
from data_models_extended import ExtendedDataService
from calculations.calculator_factory_extended import ExtendedCalculatorFactory


# --- Вспомогательные функции ---

def create_line_edit(parent, default_text="0.0", validator_params=None, tooltip=""):
    """Создает QLineEdit с валидатором и подсказкой."""
    c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
    line_edit = QLineEdit(default_text)
    if validator_params:
        validator = QDoubleValidator(*validator_params, parent)
        validator.setLocale(c_locale)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        line_edit.setValidator(validator)
    line_edit.setToolTip(tooltip)
    return line_edit

def get_float(line_edit, field_name):
    """Извлекает float из QLineEdit, обрабатывая ошибки."""
    text = line_edit.text().replace(',', '.')
    if not text:
        raise ValueError(f"Поле '{field_name}' не может быть пустым.")
    try:
        value = float(text)
        validator = line_edit.validator()
        if validator:
            state, _, _ = validator.validate(text, 0)
            if state != QDoubleValidator.State.Acceptable:
                raise ValueError(f"Некорректное числовое значение в поле '{field_name}'.")
        return value
    except ValueError:
        raise ValueError(f"Некорректное числовое значение '{text}' в поле '{field_name}'.")

def handle_error(parent, e, tab_name, formula_ref=""):
    """Обрабатывает и отображает ошибки расчета."""
    prefix = f"{tab_name} ({formula_ref}):" if formula_ref else f"{tab_name}:"
    result_text_widget = getattr(parent, "result_text", None) # Пытаемся найти result_text

    if isinstance(e, ValueError):
        QMessageBox.warning(parent, f"Ошибка ввода ({formula_ref})", str(e))
        if result_text_widget: result_text_widget.setText("Результат: Ошибка ввода.")
        logging.warning(f"{prefix} Input error - {e}")
    else:
        QMessageBox.critical(parent, f"Ошибка расчета ({formula_ref})", f"Произошла ошибка: {e}")
        if result_text_widget: result_text_widget.setText("Результат: Ошибка расчета.")
        logging.error(f"{prefix} Calculation error - {e}", exc_info=True)

# --- Вкладки ---

class ForestRestorationTab(QWidget):
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
        layout.addWidget(soil_c_group)

        # --- Выбросы от пожаров (Ф. 6) ---
        fire_group = QGroupBox("6. Выбросы ПГ от пожаров (Формула 6)")
        layout_f6 = QFormLayout(fire_group)
        self.f6_area = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Выжигаемая площадь, га")
        self.f6_fuel_mass = create_line_edit(self, "121.4", (0, 1000, 4), tooltip="Масса топлива, т/га (Таблица 25.6)")
        self.f6_comb_factor = create_line_edit(self, "0.43", (0.01, 1.0, 3), tooltip="Коэф. сгорания (0.43 верховой, 0.15 низовой)")
        self.f6_gas_type = QComboBox(); self.f6_gas_type.addItems(["CO2", "CH4", "N2O"])
        layout_f6.addRow("Площадь (A, га):", self.f6_area)
        layout_f6.addRow("Масса топлива (M_B, т/га):", self.f6_fuel_mass)
        layout_f6.addRow("Коэф. сгорания (C_f, доля):", self.f6_comb_factor)
        layout_f6.addRow("Тип газа:", self.f6_gas_type)
        calc_f6_btn = QPushButton("Рассчитать выбросы от пожара (Ф. 6)"); calc_f6_btn.clicked.connect(self._calculate_f6)
        layout_f6.addRow(calc_f6_btn)
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
        # Ф.8 N2O
        self.f8_ef = create_line_edit(self, "1.71", (0, 100, 4), tooltip="Коэф. выброса N2O, кг N/га/год")
        drain_layout.addRow("EF N2O (кг N/га/год):", self.f8_ef)
        calc_f8_btn = QPushButton("Рассчитать N2O (Ф. 8)"); calc_f8_btn.clicked.connect(self._calculate_f8)
        drain_layout.addRow(calc_f8_btn)
        # Ф.9 CH4
        self.f9_frac_ditch = create_line_edit(self, "0.025", (0, 1, 3), tooltip="Доля канав")
        self.f9_ef_land = create_line_edit(self, "4.5", (0, 1e6, 4), tooltip="EF земли, кг CH4/га/год")
        self.f9_ef_ditch = create_line_edit(self, "217", (0, 1e6, 4), tooltip="EF канав, кг CH4/га/год")
        drain_layout.addRow("Доля канав (Frac_ditch):", self.f9_frac_ditch)
        drain_layout.addRow("EF_land CH4 (кг/га/год):", self.f9_ef_land)
        drain_layout.addRow("EF_ditch CH4 (кг/га/год):", self.f9_ef_ditch)
        calc_f9_btn = QPushButton("Рассчитать CH4 (Ф. 9)"); calc_f9_btn.clicked.connect(self._calculate_f9)
        drain_layout.addRow(calc_f9_btn)
        layout.addWidget(drain_group)

        # --- Выбросы от сжигания топлива (Ф. 10) ---
        fuel_group = QGroupBox("10. Эмиссия CO2 от сжигания топлива (Формула 10)")
        # TODO: Добавить интерфейс для Ф.10 (динамические строки для разных видов топлива)
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
        calc_f12_btn = QPushButton("Перевести в CO2-экв (Ф. 12)"); calc_f12_btn.clicked.connect(self._calculate_f12)
        convert_layout.addRow(calc_f11_btn)
        convert_layout.addRow(calc_f12_btn)
        layout.addWidget(convert_group)

        # --- Результаты ---
        self.result_text = QTextEdit(); self.result_text.setReadOnly(True); self.result_text.setMaximumHeight(200)
        layout.addWidget(self.result_text)

    # --- Методы расчета для ForestRestorationTab ---
    def _calculate_f1(self):
        try:
            total_change = self.calculator.calculate_carbon_stock_change(
                get_float(self.f1_biomass, "ΔC биомасса"), get_float(self.f1_deadwood, "ΔC мертвая древесина"),
                get_float(self.f1_litter, "ΔC подстилка"), get_float(self.f1_soil, "ΔC почва")
            )
            co2_equivalent = self.calculator.carbon_to_co2(total_change)
            result = (f"Общее ΔC (Ф. 1): {total_change:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_equivalent:.4f} т CO2/год ({'Поглощение' if co2_equivalent < 0 else 'Выброс'})")
            self.result_text.setText(result); logging.info(f"ForestRestorationTab(F1): Result={total_change:.4f} t C/year")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 1")

    def _calculate_f2(self):
        try:
            delta_c = self.calculator.calculate_biomass_change(
                get_float(self.f2_c_after, "C после"), get_float(self.f2_c_before, "C до"),
                get_float(self.f2_area, "Площадь"), get_float(self.f2_period, "Период")
            )
            self.result_text.setText(f"ΔC биомассы (Ф. 2): {delta_c:.4f} т C/год")
            logging.info(f"ForestRestorationTab(F2): Result={delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 2")

    def _calculate_f3(self):
        try:
            species = self.f3_species.currentText().lower()
            diameter = get_float(self.f3_diameter, "Диаметр")
            height = get_float(self.f3_height, "Высота")
            count = self.f3_count.value()
            tree_data = ForestInventoryData(species=species, diameter=diameter, height=height, count=count)
            carbon_kg = self.calculator.calculate_tree_biomass_carbon([tree_data], fraction="всего")
            carbon_tons = carbon_kg / 1000.0
            self.result_text.setText(f"C древостоя (Ф. 3): {carbon_tons:.6f} т C ({carbon_kg:.3f} кг C)")
            logging.info(f"ForestRestorationTab(F3): Result={carbon_tons:.6f} t C")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 3")

    def _calculate_f4(self):
        try:
            heights_str = self.f4_heights.text().replace(',', ' ').split()
            heights = [float(h) for h in heights_str if h]
            species = self.f4_species.currentText().lower()
            carbon_kg = self.calculator.calculate_undergrowth_carbon(heights, species)
            carbon_tons = carbon_kg / 1000.0
            self.result_text.setText(f"C подроста (Ф. 4): {carbon_tons:.6f} т C ({carbon_kg:.3f} кг C)")
            logging.info(f"ForestRestorationTab(F4): Result={carbon_tons:.6f} t C")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 4")

    def _calculate_f5(self):
        try:
            carbon_stock = self.calculator.calculate_soil_carbon(
                get_float(self.f5_org_percent, "Орг. вещество"), get_float(self.f5_depth_cm, "Глубина"),
                get_float(self.f5_bulk_density, "Объемная масса")
            )
            self.result_text.setText(f"Запас C в почве (Ф. 5): {carbon_stock:.4f} т C/га")
            logging.info(f"ForestRestorationTab(F5): Result={carbon_stock:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 5")

    def _calculate_f6(self):
        try:
            area = get_float(self.f6_area, "Площадь пожара")
            fuel = get_float(self.f6_fuel_mass, "Масса топлива")
            comb_factor = get_float(self.f6_comb_factor, "Коэф. сгорания")
            gas = self.f6_gas_type.currentText()
            emissions = self.calculator.calculate_fire_emissions(area, fuel, comb_factor, gas)
            result = f"Выбросы от пожара (Ф. 6) {gas}: {emissions:.4f} т"
            if gas != "CO2": co2_eq = self.calculator.to_co2_equivalent(emissions, gas); result += f" (CO2-экв: {co2_eq:.4f} т)"
            self.result_text.setText(result); logging.info(f"ForestRestorationTab(F6): Result={emissions:.4f} t {gas}")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 6")

    def _calculate_f7(self):
        try:
            emission = self.calculator.calculate_drained_soil_co2(
                get_float(self.drain_area, "Площадь осушения"), get_float(self.f7_ef, "EF CO2")
            )
            self.result_text.setText(f"Выбросы CO2 от осушения (Ф. 7): {emission:.4f} т CO2/год")
            logging.info(f"ForestRestorationTab(F7): Result={emission:.4f} t CO2/year")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 7")

    def _calculate_f8(self):
        try:
            emission = self.calculator.calculate_drained_soil_n2o(
                get_float(self.drain_area, "Площадь осушения"), get_float(self.f8_ef, "EF N2O")
            )
            co2_eq = emission * 265 # GWP N2O
            self.result_text.setText(f"Выбросы N2O от осушения (Ф. 8): {emission:.6f} т N2O/год\nCO2-экв: {co2_eq:.4f} т")
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
            self.result_text.setText(f"Выбросы CH4 от осушения (Ф. 9): {emission_t:.6f} т CH4/год ({emission_kg:.3f} кг/год)\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"ForestRestorationTab(F9): Result={emission_t:.6f} t CH4/year")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 9")

    def _calculate_f11(self):
        try:
            co2_eq = self.calculator.carbon_to_co2(get_float(self.f11_carbon, "ΔC"))
            self.result_text.setText(f"Перевод ΔC в CO2 (Ф. 11): {co2_eq:.4f} т CO2")
            logging.info(f"ForestRestorationTab(F11): Result={co2_eq:.4f} t CO2")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 11")

    def _calculate_f12(self):
        try:
            co2_eq = self.calculator.to_co2_equivalent(get_float(self.f12_gas_amount, "Кол-во газа"), self.f12_gas_type.currentText())
            self.result_text.setText(f"Перевод в CO2-экв (Ф. 12): {co2_eq:.4f} т CO2-экв")
            logging.info(f"ForestRestorationTab(F12): Result={co2_eq:.4f} t CO2eq")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 12")


class AgriculturalAbsorptionTab(QWidget):
    """Вкладка для расчетов поглощения ПГ сельхозугодьями (формулы 75-90)."""

    def __init__(self, calculator: AgriculturalLandCalculator, data_service: ExtendedDataService, parent=None):
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
        self.result_text = QTextEdit(); self.result_text.setReadOnly(True); self.result_text.setMaximumHeight(150)
        main_layout.addWidget(self.result_text)

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
        lime_group = QGroupBox("Расчет C от извести (Формула 82)"); lime_layout = QFormLayout(lime_group)
        self.lime_amount = create_line_edit(self, validator_params=(0, 1e9, 4))
        lime_layout.addRow("Кол-во извести (т/год):", self.lime_amount)
        lime_calc_btn = QPushButton("Рассчитать C извести -> подставить выше"); lime_calc_btn.clicked.connect(self._calculate_lime_carbon_helper)
        lime_layout.addRow(lime_calc_btn); layout.addRow(lime_group)
        erosion_group = QGroupBox("Расчет потерь от эрозии (Формула 85)"); erosion_layout = QFormLayout(erosion_group)
        self.erosion_area = create_line_edit(self, validator_params=(0, 1e12, 4))
        erosion_layout.addRow("Площадь эрозии (га):", self.erosion_area)
        self.erosion_factor = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Коэффициент эрозии, т C/га/год")
        erosion_layout.addRow("Коэф. эрозии (т C/га/год):", self.erosion_factor)
        erosion_calc_btn = QPushButton("Рассчитать C эрозии -> подставить выше"); erosion_calc_btn.clicked.connect(self._calculate_erosion_helper)
        erosion_layout.addRow(erosion_calc_btn); layout.addRow(erosion_group)
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
        layout.addRow(resp_group)

        return widget

    def _create_organic_soil_tab(self):
        # ... (Код без изменений) ...
        widget = QWidget(); layout = QFormLayout(widget)
        self.organic_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь осушенных органогенных почв на пахотных землях.")
        layout.addRow("Площадь осушенных почв (га):", self.organic_area)
        calc_co2_btn = QPushButton("Рассчитать выбросы CO2 (Ф. 87)"); calc_co2_btn.clicked.connect(self._calculate_organic_co2)
        layout.addRow(calc_co2_btn)
        calc_n2o_btn = QPushButton("Рассчитать выбросы N2O (Ф. 88)"); calc_n2o_btn.clicked.connect(self._calculate_organic_n2o)
        layout.addRow(calc_n2o_btn)
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
        biomass_layout.addRow(calc_biomass_btn); layout.addRow(biomass_group)
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
        fire_layout.addRow(calc_fire_btn); layout.addRow(fire_group)
        return widget

    # --- Методы расчета для AgriculturalAbsorptionTab ---
    def _calculate_mineral_soil_change(self):
        try:
            c_fert=get_float(self.mineral_c_fert, "C от удобрений"); c_lime=get_float(self.mineral_c_lime, "C от извести"); c_plant=get_float(self.mineral_c_plant, "C от растений"); c_resp=get_float(self.mineral_c_resp, "C потери (дыхание)"); c_erosion=get_float(self.mineral_c_erosion, "C потери (эрозия)")
            delta_c = self.calculator.calculate_mineral_soil_carbon_change(c_fertilizer=c_fert, c_lime=c_lime, c_plant=c_plant, c_respiration=c_resp, c_erosion=c_erosion)
            co2_eq = delta_c * (-44/12)
            result = (f"ΔC в мин. почвах (Ф. 80): {delta_c:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.result_text.setText(result); logging.info(f"AgriTab: Mineral soil ΔC calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 80")

    def _calculate_lime_carbon_helper(self):
        try:
            lime_amount = get_float(self.lime_amount, "Кол-во извести"); c_lime = self.calculator.calculate_lime_carbon(lime_amount)
            self.mineral_c_lime.setText(self.c_locale.toString(c_lime, 'f', 4)); self.result_text.setText(f"C от извести (Ф. 82): {c_lime:.4f} т C/год (значение подставлено)"); logging.info(f"AgriTab: Lime carbon calculated: {c_lime:.4f} t C/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 82 (helper)")

    def _calculate_erosion_helper(self):
        try:
            area = get_float(self.erosion_area, "Площадь эрозии"); factor = get_float(self.erosion_factor, "Коэф. эрозии"); c_erosion = self.calculator.calculate_erosion_losses(area, factor)
            self.mineral_c_erosion.setText(self.c_locale.toString(c_erosion, 'f', 4)); self.result_text.setText(f"C потери (эрозия) (Ф. 85): {c_erosion:.4f} т C/год (значение подставлено)"); logging.info(f"AgriTab: Erosion loss calculated: {c_erosion:.4f} t C/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 85 (helper)")

    def _calculate_respiration_helper(self):
        try:
            area = get_float(self.f86_area, "Площадь (Ф.86)")
            rate = get_float(self.f86_rate, "Скорость эмиссии (Ф.86)")
            period = get_float(self.f86_period, "Вег. период (Ф.86)")
            c_resp = self.calculator.calculate_soil_respiration(area, rate, period)
            self.mineral_c_resp.setText(self.c_locale.toString(c_resp, 'f', 4))
            self.result_text.setText(f"C потери (дыхание) (Ф. 86): {c_resp:.4f} т C/год (значение подставлено)")
            logging.info(f"AgriTab: Respiration loss calculated: {c_resp:.4f} t C/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 86 (helper)")


    def _calculate_organic_co2(self):
        try:
            area = get_float(self.organic_area, "Площадь осушенных почв"); co2_emissions = self.calculator.calculate_organic_soil_co2(area)
            result = f"Выбросы CO2 от орган. почв (Ф. 87): {co2_emissions:.4f} т CO2/год"; self.result_text.setText(result); logging.info(f"AgriTab: Organic soil CO2 calculated: {co2_emissions:.4f} t CO2/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 87")

    def _calculate_organic_n2o(self):
        try:
            area = get_float(self.organic_area, "Площадь осушенных почв"); n2o_emissions = self.calculator.calculate_organic_soil_n2o(area); gwp_n2o = 265; co2_eq = n2o_emissions * gwp_n2o
            result = (f"Выбросы N2O от орган. почв (Ф. 88): {n2o_emissions:.6f} т N2O/год\nCO2-эквивалент: {co2_eq:.4f} т CO2-экв/год"); self.result_text.setText(result); logging.info(f"AgriTab: Organic soil N2O calculated: {n2o_emissions:.6f} t N2O/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 88")

    def _calculate_organic_ch4(self):
        try:
            area = get_float(self.organic_area, "Площадь осушенных почв"); frac_ditch = get_float(self.organic_ch4_frac_ditch, "Доля канав"); ef_land = get_float(self.organic_ch4_ef_land, "EF земли"); ef_ditch = get_float(self.organic_ch4_ef_ditch, "EF канав")
            ch4_emissions_kg = self.calculator.calculate_drained_ch4_emissions(area=area, frac_ditch=frac_ditch, ef_land=ef_land, ef_ditch=ef_ditch); ch4_emissions_tons = ch4_emissions_kg / 1000.0; gwp_ch4 = 28; co2_eq = ch4_emissions_tons * gwp_ch4
            result = (f"Выбросы CH4 от осуш. орган. почв (Ф. 75/89): {ch4_emissions_tons:.6f} т CH4/год\nCO2-эквивалент: {co2_eq:.4f} т CO2-экв/год"); self.result_text.setText(result); logging.info(f"AgriTab: Organic soil CH4 calculated: {ch4_emissions_tons:.6f} t CH4/year")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 75/89")

    def _calculate_biomass_change(self):
        try:
            gain = get_float(self.biomass_gain, "Прирост C"); loss = get_float(self.biomass_loss, "Потери C"); delta_c = self.calculator.calculate_biomass_carbon_change(gain, loss)
            co2_eq = delta_c * (-44/12)
            result = (f"ΔC биомассы (Ф. 77): {delta_c:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.result_text.setText(result); logging.info(f"AgriTab: Biomass ΔC calculated: {delta_c:.4f} t C/year")
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
            self.result_text.setText(result); logging.info(f"AgriTab: Agricultural fire emission calculated: {emission:.4f} t {gas_type}")
        except Exception as e: handle_error(self, e, "AgriculturalAbsorptionTab", "Ф. 76/90")


class PermanentForestTab(QWidget):
    """Вкладка для расчетов по постоянным лесным землям (Формулы 27-59)."""
    def __init__(self, calculator: PermanentForestCalculator, data_service: ExtendedDataService, parent=None):
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
        biomass_layout.addLayout(layout_f27)

        layout_f28 = QFormLayout()
        self.f28_carbon_stock = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Запас углерода, т C (из Ф.27 или др.)")
        self.f28_area = create_line_edit(self, validator_params=(0.001, 1e12, 4), tooltip="Площадь участка, га")
        layout_f28.addRow("Запас углерода (CP_ij, т C):", self.f28_carbon_stock)
        layout_f28.addRow("Площадь (S_ij, га):", self.f28_area)
        calc_f28_btn = QPushButton("Рассчитать средний C/га (Ф. 28)"); calc_f28_btn.clicked.connect(self._calculate_f28)
        layout_f28.addRow(calc_f28_btn)
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
        deadwood_layout.addLayout(layout_f36)
        # TODO: Добавить интерфейс для Ф. 37-42
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
        litter_layout.addLayout(layout_f43)
        # TODO: Добавить интерфейс для Ф. 44-48
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
        soil_layout.addLayout(layout_f49)
        # TODO: Добавить интерфейс для Ф. 50-54
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
        # Ф.57 N2O
        self.f57_ef = create_line_edit(self, "1.71", (0, 100, 4), tooltip="Коэф. выброса N2O, кг N/га/год")
        layout_f56_58.addRow("EF N2O (кг N/га/год):", self.f57_ef)
        calc_f57_btn = QPushButton("Рассчитать N2O от осушения (Ф. 57)"); calc_f57_btn.clicked.connect(self._calculate_f57)
        layout_f56_58.addRow(calc_f57_btn)
        # Ф.58 CH4
        self.f58_frac_ditch = create_line_edit(self, "0.025", (0, 1, 3), tooltip="Доля канав")
        self.f58_ef_land = create_line_edit(self, "4.5", (0, 1e6, 4), tooltip="EF земли, кг CH4/га/год")
        self.f58_ef_ditch = create_line_edit(self, "217", (0, 1e6, 4), tooltip="EF канав, кг CH4/га/год")
        layout_f56_58.addRow("Доля канав (Frac_ditch):", self.f58_frac_ditch)
        layout_f56_58.addRow("EF_land CH4 (кг/га/год):", self.f58_ef_land)
        layout_f56_58.addRow("EF_ditch CH4 (кг/га/год):", self.f58_ef_ditch)
        calc_f58_btn = QPushButton("Рассчитать CH4 от осушения (Ф. 58)"); calc_f58_btn.clicked.connect(self._calculate_f58)
        layout_f56_58.addRow(calc_f58_btn)
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
        emissions_layout.addLayout(fire_layout)

        main_layout.addWidget(emissions_group)

        # --- Результаты ---
        self.result_text = QTextEdit("Здесь будут результаты расчетов...")
        self.result_text.setReadOnly(True); self.result_text.setMaximumHeight(200)
        main_layout.addWidget(self.result_text)

    # --- Методы расчета для PermanentForestTab ---
    def _calculate_f27(self):
        try:
            volume = get_float(self.f27_volume, "Запас древесины (Ф.27)")
            factor = get_float(self.f27_conversion_factor, "Коэф. перевода (Ф.27)")
            carbon_stock = self.calculator.calculate_biomass_carbon_stock(volume, factor)
            self.result_text.setText(f"Запас углерода в биомассе (Ф. 27): {carbon_stock:.4f} т C")
            logging.info(f"PermanentForestTab: F27 calculated: {carbon_stock:.4f} t C")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 27")

    def _calculate_f28(self):
        try:
            carbon_stock = get_float(self.f28_carbon_stock, "Запас углерода (Ф.28)")
            area = get_float(self.f28_area, "Площадь (Ф.28)")
            mean_carbon = self.calculator.calculate_mean_carbon_per_hectare(carbon_stock, area)
            self.result_text.setText(f"Средний запас C/га (Ф. 28): {mean_carbon:.4f} т C/га")
            logging.info(f"PermanentForestTab: F28 calculated: {mean_carbon:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 28")

    def _calculate_f35(self):
        try:
            absorption = get_float(self.f35_absorption, "Абсорбция (Ф.35)")
            harvest_loss = get_float(self.f35_harvest_loss, "Потери от рубок (Ф.35)")
            fire_loss = get_float(self.f35_fire_loss, "Потери от пожаров (Ф.35)")
            budget = self.calculator.calculate_biomass_budget(absorption, harvest_loss, fire_loss)
            co2_eq = budget * (-44/12)
            result = (f"Бюджет биомассы (Ф. 35): {budget:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.result_text.setText(result); logging.info(f"PermanentForestTab: F35 calculated: {budget:.4f} t C/year")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 35")

    def _calculate_f36(self):
        try:
            volume = get_float(self.f36_volume, "Запас древесины (Ф.36)")
            factor = get_float(self.f36_conversion_factor, "Коэф. перевода мертв.др. (Ф.36)")
            carbon_stock = self.calculator.calculate_deadwood_carbon_stock(volume, factor)
            self.result_text.setText(f"Запас углерода в мертвой древесине (Ф. 36): {carbon_stock:.4f} т C")
            logging.info(f"PermanentForestTab: F36 calculated: {carbon_stock:.4f} t C")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 36")

    def _calculate_f43(self):
        try:
            area = get_float(self.f43_area, "Площадь (Ф.43)")
            factor = get_float(self.f43_litter_factor, "Коэф. C подстилки (Ф.43)")
            carbon_stock = self.calculator.calculate_litter_carbon_stock(area, factor)
            self.result_text.setText(f"Запас углерода в подстилке (Ф. 43): {carbon_stock:.4f} т C")
            logging.info(f"PermanentForestTab: F43 calculated: {carbon_stock:.4f} t C")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 43")

    def _calculate_f49(self):
        try:
            area = get_float(self.f49_area, "Площадь (Ф.49)")
            factor = get_float(self.f49_soil_factor, "Коэф. C почвы (Ф.49)")
            carbon_stock = self.calculator.calculate_soil_carbon_stock(area, factor)
            self.result_text.setText(f"Запас углерода в почве (Ф. 49): {carbon_stock:.4f} т C")
            logging.info(f"PermanentForestTab: F49 calculated: {carbon_stock:.4f} t C")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 49")

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
            self.result_text.setText(result)
            logging.info(f"PermanentForestTab: F55 calculated: {total_budget:.4f} t C/year")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 55")

    def _calculate_f56(self):
        try:
            area = get_float(self.f56_58_area, "Площадь осушения (Ф.56)")
            ef = get_float(self.f56_ef, "Коэф. выброса (Ф.56)")
            co2_emission = self.calculator.calculate_drained_forest_co2(area, ef)
            self.result_text.setText(f"Выбросы CO2 от осушения (Ф. 56): {co2_emission:.4f} т CO2/год")
            logging.info(f"PermanentForestTab: F56 calculated: {co2_emission:.4f} t CO2/year")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 56")

    def _calculate_f57(self):
        try:
            area = get_float(self.f56_58_area, "Площадь осушения (Ф.57)")
            ef = get_float(self.f57_ef, "Коэф. выброса N2O (Ф.57)")
            n2o_emission = self.calculator.calculate_drained_forest_n2o(area, ef)
            co2_eq = n2o_emission * 265
            self.result_text.setText(f"Выбросы N2O от осушения (Ф. 57): {n2o_emission:.6f} т N2O/год\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"PermanentForestTab: F57 calculated: {n2o_emission:.6f} t N2O/year")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 57")

    def _calculate_f58(self):
        try:
            area = get_float(self.f56_58_area, "Площадь осушения (Ф.58)")
            frac_ditch = get_float(self.f58_frac_ditch, "Доля канав (Ф.58)")
            ef_land = get_float(self.f58_ef_land, "EF_land CH4 (Ф.58)")
            ef_ditch = get_float(self.f58_ef_ditch, "EF_ditch CH4 (Ф.58)")
            ch4_emission_kg = self.calculator.calculate_drained_forest_ch4(area, frac_ditch, ef_land, ef_ditch)
            ch4_emission_t = ch4_emission_kg / 1000.0
            co2_eq = ch4_emission_t * 28
            self.result_text.setText(f"Выбросы CH4 от осушения (Ф. 58): {ch4_emission_t:.6f} т CH4/год ({ch4_emission_kg:.3f} кг/год)\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"PermanentForestTab: F58 calculated: {ch4_emission_t:.6f} t CH4/year")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 58")

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
            self.result_text.setText(result); logging.info(f"PermanentForestTab: F59 calculated: {emission:.4f} t {gas_type}")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 59")


class ProtectiveForestTab(QWidget):
    """Вкладка для расчетов по защитным насаждениям (Формулы 60-74)."""
    def __init__(self, calculator: ProtectiveForestCalculator, data_service: ExtendedDataService, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.data_service = data_service
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self.carbon_stocks_biomass = [] # Для хранения CPA_ijl (Ф.61)
        self.carbon_stocks_deadwood = [] # Для хранения CPD_ijl (Ф.64)
        self.carbon_stocks_litter = [] # Для хранения CPL_ijl (Ф.67)
        self.carbon_stocks_soil = [] # Для хранения CPS_ijl (Ф.70)
        self._init_ui()
        logging.info("ProtectiveForestTab initialized.")

    def _init_ui(self):
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget); main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(main_widget)
        outer_layout = QVBoxLayout(self); outer_layout.addWidget(scroll_area)

        # --- Динамика запасов по годам (Ф. 60, 63, 66, 69) ---
        dynamics_group = QGroupBox("Динамика запасов C по годам создания (Ф. 60, 63, 66, 69)")
        dynamics_layout = QVBoxLayout(dynamics_group)
        # Интерфейс для добавления/отображения данных по годам (можно использовать QTableWidget)
        self.dynamics_table = QTableWidget()
        self.dynamics_table.setColumnCount(5) # Год, Площадь, Ср.C биом, Ср.C мер.орг, Ср.C подст, Ср.C почва
        self.dynamics_table.setHorizontalHeaderLabels(["Год", "Площадь(га)", "Ср.C Биом(т/га)", "Ср.C Мертв(т/га)", "Ср.C Подст(т/га)", "Ср.C Почва(т/га)"])
        # TODO: Добавить кнопки добавления/удаления строк в таблицу
        dynamics_layout.addWidget(self.dynamics_table)
        calc_dynamics_btn = QPushButton("Рассчитать запасы по годам (Ф. 60, 63, 66, 69)"); calc_dynamics_btn.clicked.connect(self._calculate_dynamics)
        dynamics_layout.addWidget(calc_dynamics_btn)
        main_layout.addWidget(dynamics_group)

        # --- Суммарные запасы (Ф. 61, 64, 67, 70) ---
        sum_group = QGroupBox("Суммарные запасы углерода (Ф. 61, 64, 67, 70)")
        sum_layout = QFormLayout(sum_group)
        self.f61_result = QLineEdit(); self.f61_result.setReadOnly(True)
        self.f64_result = QLineEdit(); self.f64_result.setReadOnly(True)
        self.f67_result = QLineEdit(); self.f67_result.setReadOnly(True)
        self.f70_result = QLineEdit(); self.f70_result.setReadOnly(True)
        sum_layout.addRow("Сумма C биомассы (CPA_ij, т C):", self.f61_result)
        sum_layout.addRow("Сумма C мертв. орг. (CPD_ij, т C):", self.f64_result)
        sum_layout.addRow("Сумма C подстилки (CPL_ij, т C):", self.f67_result)
        sum_layout.addRow("Сумма C почвы (CPS_ij, т C):", self.f70_result)
        main_layout.addWidget(sum_group)

        # --- Годичное накопление (Ф. 62, 65, 68, 71) ---
        accum_group = QGroupBox("Годичное накопление углерода (Ф. 62, 65, 68, 71)")
        layout_accum = QFormLayout(accum_group)
        self.accum_c_next_year = QLineEdit(); self.accum_c_next_year.setReadOnly(True); self.accum_c_next_year.setPlaceholderText("Сумма C (i+1)")
        self.accum_c_current_year = QLineEdit(); self.accum_c_current_year.setReadOnly(True); self.accum_c_current_year.setPlaceholderText("Сумма C (i)")
        layout_accum.addRow("Запасы C след. года (т C):", self.accum_c_next_year) # Упрощенный ввод для примера
        layout_accum.addRow("Запасы C текущ. года (т C):", self.accum_c_current_year) # Упрощенный ввод для примера
        calc_accum_btn = QPushButton("Рассчитать накопление (Ф. 62, 65, 68, 71)"); calc_accum_btn.clicked.connect(self._calculate_accumulation)
        layout_accum.addRow(calc_accum_btn)
        # Поля для вывода результатов Ф.62, 65, 68, 71
        self.f62_result = QLineEdit(); self.f62_result.setReadOnly(True)
        self.f65_result = QLineEdit(); self.f65_result.setReadOnly(True)
        self.f68_result = QLineEdit(); self.f68_result.setReadOnly(True)
        self.f71_result = QLineEdit(); self.f71_result.setReadOnly(True)
        layout_accum.addRow("Накопление биомасса (CPAS, т C/год):", self.f62_result)
        layout_accum.addRow("Накопление мертв.орг. (CPDS, т C/год):", self.f65_result)
        layout_accum.addRow("Накопление подстилка (CPLS, т C/год):", self.f68_result)
        layout_accum.addRow("Накопление почва (CPSS, т C/год):", self.f71_result)
        main_layout.addWidget(accum_group)

        # --- Общее накопление (Ф. 72) ---
        total_accum_group = QGroupBox("Общее накопление углерода (Формула 72)")
        layout_f72 = QFormLayout(total_accum_group)
        # Используем результаты из предыдущего блока
        layout_f72.addRow("Накопление биомасса (CPAS, т C/год):", self.f62_result)
        layout_f72.addRow("Накопление мертв.орг. (CPDS, т C/год):", self.f65_result)
        layout_f72.addRow("Накопление подстилка (CPLS, т C/год):", self.f68_result)
        layout_f72.addRow("Накопление почва (CPSS, т C/год):", self.f71_result)
        calc_f72_btn = QPushButton("Рассчитать общее накопление (Ф. 72)"); calc_f72_btn.clicked.connect(self._calculate_f72)
        layout_f72.addRow(calc_f72_btn)
        main_layout.addWidget(total_accum_group)

        # --- Выбросы от осушения (Ф. 73, 74) ---
        drain_group = QGroupBox("Выбросы от осушения переведенных земель (Формулы 73, 74)")
        layout_drain = QFormLayout(drain_group)
        self.f73_74_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь осушенных переведенных земель, га")
        layout_drain.addRow("Площадь осушения (A, га):", self.f73_74_area)
        # Ф.73 CO2
        self.f73_ef = create_line_edit(self, "0.71", (0, 100, 4), tooltip="Коэф. выброса CO2, т C/га/год (как для лесных)")
        layout_drain.addRow("EF CO2 (т C/га/год):", self.f73_ef)
        calc_f73_btn = QPushButton("Рассчитать CO2 от осушения (Ф. 73)"); calc_f73_btn.clicked.connect(self._calculate_f73)
        layout_drain.addRow(calc_f73_btn)
        # Ф.74 N2O
        self.f74_ef = create_line_edit(self, "1.71", (0, 100, 4), tooltip="Коэф. выброса N2O, кг N/га/год (как для лесных)")
        layout_drain.addRow("EF N2O (кг N/га/год):", self.f74_ef)
        calc_f74_btn = QPushButton("Рассчитать N2O от осушения (Ф. 74)"); calc_f74_btn.clicked.connect(self._calculate_f74)
        layout_drain.addRow(calc_f74_btn)
        main_layout.addWidget(drain_group)

        # --- Результаты ---
        self.result_text = QTextEdit("Здесь будут результаты расчетов...")
        self.result_text.setReadOnly(True); self.result_text.setMaximumHeight(150)
        main_layout.addWidget(self.result_text)

    # --- Методы расчета для ProtectiveForestTab ---
    def _calculate_dynamics(self):
        # TODO: Считать данные из таблицы self.dynamics_table
        # Рассчитать запасы для каждого года по Ф. 60, 63, 66, 69
        # Сохранить результаты в self.carbon_stocks_...
        # Обновить поля Ф. 61, 64, 67, 70
        try:
            # Заглушка - расчет только для биомассы первого года
            if self.dynamics_table.rowCount() > 0:
                 area = float(self.dynamics_table.item(0, 1).text().replace(',', '.'))
                 mean_c = float(self.dynamics_table.item(0, 2).text().replace(',', '.'))
                 stock = self.calculator.calculate_protective_biomass_dynamics(area, mean_c)
                 # Обновляем ячейку или выводим результат
                 self.f61_result.setText(f"{stock:.4f}") # Показываем только первую строку как сумму
                 self.result_text.setText(f"Пример расчета запаса C биомассы (Ф. 60) для 1 строки: {stock:.4f} т C\n"
                                          f"(Полный расчет и суммирование не реализованы)")
                 logging.info(f"ProtectiveForestTab(F60-example): Result={stock:.4f} t C")
            else:
                QMessageBox.warning(self, "Нет данных", "Добавьте данные по годам в таблицу.")
        except Exception as e: handle_error(self, e, "ProtectiveForestTab", "Ф. 60/63/66/69")

    def _calculate_accumulation(self):
        # TODO: Получить суммарные запасы за два года (current, next)
        # Рассчитать накопление по Ф. 62, 65, 68, 71
        # Обновить поля self.f62_result и т.д.
        try:
             # Заглушка - расчет только для биомассы
            c_next = get_float(self.accum_c_next_year, "Запас C след. года")
            c_curr = get_float(self.accum_c_current_year, "Запас C текущ. года")
            acc = self.calculator.calculate_protective_biomass_absorption(c_next, c_curr)
            self.f62_result.setText(f"{acc:.4f}")
            self.result_text.setText(f"Пример расчета накопления C биомассы (Ф. 62): {acc:.4f} т C/год\n"
                                     f"(Расчет для других пулов не реализован)")
            logging.info(f"ProtectiveForestTab(F62-example): Result={acc:.4f} t C/year")
        except Exception as e: handle_error(self, e, "ProtectiveForestTab", "Ф. 62/65/68/71")


    def _calculate_f72(self):
        try:
            acc_b = get_float(self.f62_result, "Накопление биомасса (Ф.72)")
            acc_d = get_float(self.f65_result, "Накопление мертв.орг. (Ф.72)") # Может быть пустым
            acc_l = get_float(self.f68_result, "Накопление подстилка (Ф.72)") # Может быть пустым
            acc_s = get_float(self.f71_result, "Накопление почва (Ф.72)")     # Может быть пустым
            total_acc = self.calculator.calculate_protective_total_accumulation(acc_b, acc_d, acc_l, acc_s)
            co2_eq = total_acc * (-44/12)
            result = (f"Общее накопление (Ф. 72):\nCPS = {total_acc:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.result_text.setText(result); logging.info(f"ProtectiveForestTab: F72 calculated: {total_acc:.4f} t C/year")
        except Exception as e: handle_error(self, e, "ProtectiveForestTab", "Ф. 72")

    def _calculate_f73(self):
        try:
            area = get_float(self.f73_74_area, "Площадь осушения (Ф.73)")
            ef = get_float(self.f73_ef, "EF CO2 (Ф.73)")
            emission = self.calculator.calculate_converted_land_co2(area, ef) # Используем метод из калькулятора
            self.result_text.setText(f"Выбросы CO2 от осушения (Ф. 73): {emission:.4f} т CO2/год")
            logging.info(f"ProtectiveForestTab(F73): Result={emission:.4f} t CO2/year")
        except Exception as e: handle_error(self, e, "ProtectiveForestTab", "Ф. 73")

    def _calculate_f74(self):
        try:
            area = get_float(self.f73_74_area, "Площадь осушения (Ф.74)")
            ef = get_float(self.f74_ef, "EF N2O (Ф.74)")
            emission = self.calculator.calculate_converted_land_n2o(area, ef) # Используем метод из калькулятора
            co2_eq = emission * 265
            self.result_text.setText(f"Выбросы N2O от осушения (Ф. 74): {emission:.6f} т N2O/год\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"ProtectiveForestTab(F74): Result={emission:.6f} t N2O/year")
        except Exception as e: handle_error(self, e, "ProtectiveForestTab", "Ф. 74")


class LandReclamationTab(QWidget):
    """Вкладка для расчетов по рекультивации земель (Формулы 13-26)."""
    def __init__(self, calculator: LandReclamationCalculator, data_service: ExtendedDataService, parent=None):
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
        change_layout.addLayout(layout_f14)
        layout_f15 = QFormLayout()
        self.f15_soil_after = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас C в почве ПОСЛЕ рекультивации, т C/га")
        self.f15_soil_before = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас C в почве ДО рекультивации, т C/га")
        layout_f15.addRow("C почвы ПОСЛЕ (т C/га):", self.f15_soil_after)
        layout_f15.addRow("C почвы ДО (т C/га):", self.f15_soil_before)
        calc_f15_btn = QPushButton("Рассчитать ΔC почвы (Ф. 15)"); calc_f15_btn.clicked.connect(self._calculate_f15)
        layout_f15.addRow(calc_f15_btn)
        change_layout.addLayout(layout_f15)
        layout_f13 = QFormLayout()
        self.f13_biomass_change_res = QLineEdit(); self.f13_biomass_change_res.setReadOnly(True); self.f13_biomass_change_res.setPlaceholderText("Результат Ф.14")
        self.f13_soil_change_res = QLineEdit(); self.f13_soil_change_res.setReadOnly(True); self.f13_soil_change_res.setPlaceholderText("Результат Ф.15")
        layout_f13.addRow("ΔC биомасса (т C/год):", self.f13_biomass_change_res)
        layout_f13.addRow("ΔC почва (т C/год):", self.f13_soil_change_res)
        calc_f13_btn = QPushButton("Рассчитать ΔC рекультивации (Ф. 13)"); calc_f13_btn.clicked.connect(self._calculate_f13)
        layout_f13.addRow(calc_f13_btn)
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
        grass_layout.addLayout(layout_f22)
        layout_f20 = QFormLayout()
        self.f20_aboveground_res = QLineEdit(); self.f20_aboveground_res.setReadOnly(True); self.f20_aboveground_res.setPlaceholderText("Результат Ф.21")
        self.f20_belowground_res = QLineEdit(); self.f20_belowground_res.setReadOnly(True); self.f20_belowground_res.setPlaceholderText("Результат Ф.22")
        layout_f20.addRow("C надземной (т C/га):", self.f20_aboveground_res)
        layout_f20.addRow("C подземной (т C/га):", self.f20_belowground_res)
        calc_f20_btn = QPushButton("Рассчитать общий C трав. биомассы (Ф. 20)"); calc_f20_btn.clicked.connect(self._calculate_f20)
        layout_f20.addRow(calc_f20_btn)
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
        main_layout.addWidget(soil_c_group)

        # --- Выбросы от сжигания топлива (Ф. 24) ---
        fuel_group = QGroupBox("24. Эмиссия CO2 от сжигания топлива (Формула 24)")
        # TODO: Добавить интерфейс для Ф.24 (динамические строки)
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
        calc_f26_btn = QPushButton("Перевести в CO2-экв (Ф. 26)"); calc_f26_btn.clicked.connect(self._calculate_f26)
        convert_layout.addRow(calc_f25_btn)
        convert_layout.addRow(calc_f26_btn)
        main_layout.addWidget(convert_group)

        # --- Результаты ---
        self.result_text = QTextEdit("Здесь будут результаты расчетов...")
        self.result_text.setReadOnly(True); self.result_text.setMaximumHeight(150)
        main_layout.addWidget(self.result_text)

    # --- Методы расчета для LandReclamationTab ---
    def _calculate_f14(self):
        try:
            c_after = get_float(self.f14_c_after, "C биомассы ПОСЛЕ (Ф.14)"); c_before = get_float(self.f14_c_before, "C биомассы ДО (Ф.14)")
            area = get_float(self.f14_15_area, "Площадь (Ф.14)"); period = get_float(self.f14_15_period, "Период (Ф.14)")
            delta_c = self.calculator.calculate_reclamation_biomass_change(c_after, c_before, area, period)
            self.f13_biomass_change_res.setText(f"{delta_c:.4f}")
            self.result_text.setText(f"ΔC биомассы (Ф. 14): {delta_c:.4f} т C/год")
            logging.info(f"LandReclamationTab: F14 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 14")

    def _calculate_f15(self):
        try:
            soil_after = get_float(self.f15_soil_after, "C почвы ПОСЛЕ (Ф.15)"); soil_before = get_float(self.f15_soil_before, "C почвы ДО (Ф.15)")
            area = get_float(self.f14_15_area, "Площадь (Ф.15)"); period = get_float(self.f14_15_period, "Период (Ф.15)")
            delta_c = self.calculator.calculate_reclamation_soil_change(soil_after, soil_before, area, period)
            self.f13_soil_change_res.setText(f"{delta_c:.4f}")
            self.result_text.setText(f"ΔC почвы (Ф. 15): {delta_c:.4f} т C/год")
            logging.info(f"LandReclamationTab: F15 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 15")

    def _calculate_f13(self):
        try:
            biomass_change = get_float(self.f13_biomass_change_res, "ΔC биомасса (из Ф.14)")
            soil_change = get_float(self.f13_soil_change_res, "ΔC почва (из Ф.15)")
            delta_c = self.calculator.calculate_conversion_carbon_change(biomass_change, soil_change) # Метод калькулятора назван так
            co2_eq = delta_c * (-44/12)
            result = (f"ΔC рекультивации (Ф. 13):\nΔC = {delta_c:.4f} т C/год\nЭквивалент CO2: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.result_text.setText(result); logging.info(f"LandReclamationTab: F13 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 13")

    def _calculate_f21(self):
        try:
            dry_weight = get_float(self.f21_dry_weight, "Сухой вес пробы (Ф.21)")
            carbon = self.calculator.calculate_aboveground_grass_carbon(dry_weight)
            self.f20_aboveground_res.setText(f"{carbon:.4f}") # Помещаем результат в поле для Ф.20
            self.f22_aboveground_c.setText(f"{carbon:.4f}") # И в поле для Ф.22
            self.result_text.setText(f"C надземной трав. биомассы (Ф. 21): {carbon:.4f} т C/га")
            logging.info(f"LandReclamationTab: F21 calculated: {carbon:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 21")

    def _calculate_f22(self):
        try:
            above_c = get_float(self.f22_aboveground_c, "C надземной (Ф.22)")
            a = get_float(self.f22_a, "Коэффициент a (Ф.22)")
            b = get_float(self.f22_b, "Коэффициент b (Ф.22)")
            carbon = self.calculator.calculate_belowground_grass_carbon(above_c, a, b)
            self.f20_belowground_res.setText(f"{carbon:.4f}") # Помещаем результат в поле для Ф.20
            self.result_text.setText(f"C подземной трав. биомассы (Ф. 22): {carbon:.4f} т C/га")
            logging.info(f"LandReclamationTab: F22 calculated: {carbon:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 22")

    def _calculate_f20(self):
        try:
            above_c = get_float(self.f20_aboveground_res, "C надземной (из Ф.21)")
            below_c = get_float(self.f20_belowground_res, "C подземной (из Ф.22)")
            total_c = self.calculator.calculate_grassland_carbon(above_c, below_c)
            self.result_text.setText(f"Общий C трав. биомассы (Ф. 20): {total_c:.4f} т C/га")
            logging.info(f"LandReclamationTab: F20 calculated: {total_c:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 20")

    def _calculate_f23(self):
        try:
            org_perc = get_float(self.f23_org_percent, "Орг. вещество (Ф.23)"); depth = get_float(self.f23_depth_cm, "Глубина (Ф.23)"); density = get_float(self.f23_bulk_density, "Объемная масса (Ф.23)")
            carbon_stock = self.calculator.calculate_soil_carbon_from_organic(org_perc, depth, density)
            self.result_text.setText(f"Запас C в почве (Ф. 23): {carbon_stock:.4f} т C/га")
            logging.info(f"LandReclamationTab: F23 calculated: {carbon_stock:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 23")

    def _calculate_f25(self):
        try:
            co2_eq = self.calculator.carbon_to_co2_conversion(get_float(self.f25_carbon, "ΔC (Ф.25)"))
            self.result_text.setText(f"Перевод ΔC в CO2 (Ф. 25): {co2_eq:.4f} т CO2")
            logging.info(f"LandReclamationTab(F25): Result={co2_eq:.4f} t CO2")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 25")

    def _calculate_f26(self):
        try:
            co2_eq = self.calculator.ghg_to_co2_equivalent(get_float(self.f26_gas_amount, "Кол-во газа (Ф.26)"), self.f26_gas_type.currentText())
            self.result_text.setText(f"Перевод в CO2-экв (Ф. 26): {co2_eq:.4f} т CO2-экв")
            logging.info(f"LandReclamationTab(F26): Result={co2_eq:.4f} t CO2eq")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 26")


class LandConversionTab(QWidget):
    """Вкладка для расчетов по конверсии земель и кормовым угодьям (Формулы 91-100)."""
    def __init__(self, calculator: LandConversionCalculator, data_service: ExtendedDataService, parent=None):
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
        calc_f93_btn = QPushButton("Рассчитать N2O от осушения (Ф. 93)"); calc_f93_btn.clicked.connect(self._calculate_f93)
        layout_92_94.addRow(calc_f93_btn)
        # Ф.94 CH4
        self.f94_frac_ditch = create_line_edit(self, "0.5", (0, 1, 3), tooltip="Доля канав (как для пашни)")
        self.f94_ef_land = create_line_edit(self, "0.0", (0, 1e6, 4), tooltip="EF земли, кг CH4/га/год (как для пашни)")
        self.f94_ef_ditch = create_line_edit(self, "1165", (0, 1e6, 4), tooltip="EF канав, кг CH4/га/год (как для пашни)")
        layout_92_94.addRow("Доля канав (Frac_ditch):", self.f94_frac_ditch)
        layout_92_94.addRow("EF_land CH4 (кг/га/год):", self.f94_ef_land)
        layout_92_94.addRow("EF_ditch CH4 (кг/га/год):", self.f94_ef_ditch)
        calc_f94_btn = QPushButton("Рассчитать CH4 от осушения (Ф. 94)"); calc_f94_btn.clicked.connect(self._calculate_f94)
        layout_92_94.addRow(calc_f94_btn)
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
        grass_layout.addLayout(layout_f96)

        # Ф. 97: Поступление C от растений
        layout_f97 = QFormLayout()
        self.f97_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь кормовых угодий, га")
        self.f97_c_acc = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Аккумуляция углерода, т C/га/год")
        layout_f97.addRow("Площадь (A, га):", self.f97_area)
        layout_f97.addRow("Аккумуляция C (C_акк, т C/га/год):", self.f97_c_acc)
        calc_f97_btn = QPushButton("Рассчитать C растения (Ф. 97) -> подставить в Ф.96"); calc_f97_btn.clicked.connect(self._calculate_f97)
        layout_f97.addRow(calc_f97_btn)
        grass_layout.addLayout(layout_f97)

        # Ф. 98: Поступление C с навозом - Упрощенный интерфейс
        layout_f98 = QFormLayout()
        self.f98_manure_c = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Общее поступление C с навозом, т C/год (рассчитайте отдельно)")
        layout_f98.addRow("C навоз (Cmanure, т C/год):", self.f98_manure_c)
        # TODO: Добавить интерфейс для ввода данных по животным (LivestockData)
        grass_layout.addLayout(layout_f98)

        # Ф. 99: Потери от эрозии
        layout_f99 = QFormLayout()
        self.f99_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь пастбищ, га")
        self.f99_erosion_factor = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Коэффициент эрозии, т C/га/год")
        layout_f99.addRow("Площадь (A, га):", self.f99_area)
        layout_f99.addRow("Коэф. эрозии (EFerosion, т C/га/год):", self.f99_erosion_factor)
        calc_f99_btn = QPushButton("Рассчитать C эрозии (Ф. 99) -> подставить в Ф.96"); calc_f99_btn.clicked.connect(self._calculate_f99)
        layout_f99.addRow(calc_f99_btn)
        grass_layout.addLayout(layout_f99)

        # Ф. 100: Вынос C с сеном
        layout_f100 = QFormLayout()
        self.f100_hay_yield = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Годовая урожайность сена, т/год")
        layout_f100.addRow("Урожайность сена (Yhay, т/год):", self.f100_hay_yield)
        calc_f100_btn = QPushButton("Рассчитать вынос C (Ф. 100) -> подставить в Ф.96"); calc_f100_btn.clicked.connect(self._calculate_f100)
        layout_f100.addRow(calc_f100_btn)
        grass_layout.addLayout(layout_f100)

        main_layout.addWidget(grass_group)

        # --- Результаты ---
        self.result_text = QTextEdit("Здесь будут результаты расчетов...")
        self.result_text.setReadOnly(True); self.result_text.setMaximumHeight(150)
        main_layout.addWidget(self.result_text)

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
            self.result_text.setText(result); logging.info(f"LandConversionTab: F91 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 91")

    def _calculate_f92(self):
        try:
            area = get_float(self.f92_94_area, "Площадь осушения (Ф.92)")
            ef = get_float(self.f92_ef, "EF CO2 (Ф.92)")
            emission = self.calculator.calculate_converted_land_co2(area, ef)
            self.result_text.setText(f"Выбросы CO2 от осушения (Ф. 92): {emission:.4f} т CO2/год")
            logging.info(f"LandConversionTab(F92): Result={emission:.4f} t CO2/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 92")

    def _calculate_f93(self):
        try:
            area = get_float(self.f92_94_area, "Площадь осушения (Ф.93)")
            ef = get_float(self.f93_ef, "EF N2O (Ф.93)")
            emission = self.calculator.calculate_converted_land_n2o(area, ef)
            co2_eq = emission * 265
            self.result_text.setText(f"Выбросы N2O от осушения (Ф. 93): {emission:.6f} т N2O/год\nCO2-экв: {co2_eq:.4f} т")
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
            self.result_text.setText(f"Выбросы CH4 от осушения (Ф. 94): {emission_t:.6f} т CH4/год ({emission_kg:.3f} кг/год)\nCO2-экв: {co2_eq:.4f} т")
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
            self.result_text.setText(result); logging.info(f"LandConversionTab(F95): Result={emission:.4f} t {gas_type}")
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
            self.result_text.setText(result); logging.info(f"LandConversionTab: F96 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 96")

    def _calculate_f97(self):
        try:
            area = get_float(self.f97_area, "Площадь (Ф.97)")
            c_acc = get_float(self.f97_c_acc, "Аккумуляция C (Ф.97)")
            c_plant = self.calculator.calculate_grassland_plant_carbon(area, c_acc)
            self.f96_c_plant.setText(self.c_locale.toString(c_plant, 'f', 4))
            self.result_text.setText(f"C растения (Ф. 97): {c_plant:.4f} т C/год (значение подставлено в Ф.96)")
            logging.info(f"LandConversionTab: F97 calculated: {c_plant:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 97")

    def _calculate_f99(self):
        try:
            area = get_float(self.f99_area, "Площадь (Ф.99)")
            factor = get_float(self.f99_erosion_factor, "Коэф. эрозии (Ф.99)")
            c_erosion = self.calculator.calculate_grassland_erosion(area, factor)
            self.f96_c_erosion.setText(self.c_locale.toString(c_erosion, 'f', 4))
            self.result_text.setText(f"C эрозия (Ф. 99): {c_erosion:.4f} т C/год (значение подставлено в Ф.96)")
            logging.info(f"LandConversionTab: F99 calculated: {c_erosion:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 99")

    def _calculate_f100(self):
        try:
            hay_yield = get_float(self.f100_hay_yield, "Урожайность сена (Ф.100)")
            carbon_removal = self.calculator.calculate_hay_carbon_removal(hay_yield)
            self.f96_c_hay.setText(self.c_locale.toString(carbon_removal, 'f', 4))
            self.result_text.setText(f"Вынос C с сеном (Ф. 100): {carbon_removal:.4f} т C/год (значение подставлено в Ф.96)")
            logging.info(f"LandConversionTab: F100 calculated: {carbon_removal:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 100")


class AbsorptionSummaryTab(QWidget):
    """Вкладка для сводного расчета поглощения."""
    def __init__(self, factory: ExtendedCalculatorFactory, parent=None):
        super().__init__(parent)
        self.factory = factory
        self._init_ui()
        logging.info("AbsorptionSummaryTab initialized.")

    def _init_ui(self):
        main_layout = QVBoxLayout(self); main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        label = QLabel("Сводный расчет поглощения"); label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(label)
        self.summary_button = QPushButton("Собрать данные и рассчитать итог"); self.summary_button.clicked.connect(self._calculate_summary)
        main_layout.addWidget(self.summary_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.result_text = QTextEdit("Нажмите кнопку для расчета сводного поглощения...\n(Функционал сбора данных не реализован)")
        self.result_text.setReadOnly(True)
        main_layout.addWidget(self.result_text)

    def _calculate_summary(self):
        try:
            logging.info("Calculating absorption summary...")
            total_absorption_c = 0.0; total_emission_co2 = 0.0; total_emission_ch4 = 0.0; total_emission_n2o = 0.0
            # --- Шаг 1: Сбор данных из других вкладок (НЕ РЕАЛИЗОВАН) ---
            QMessageBox.warning(self, "Внимание", "Расчет выполнен с примерными данными.\nФункционал сбора данных со вкладок не реализован.")
            # Используем заглушки
            total_absorption_c = 150.0 # Пример: поглотили 150 т C
            total_emission_co2 = 10.0  # Пример: выбросили 10 т CO2 от осушения
            total_emission_ch4 = 0.5   # Пример: выбросили 0.5 т CH4 от пожаров/осушения
            total_emission_n2o = 0.1   # Пример: выбросили 0.1 т N2O от осушения
            # --- Шаг 2: Расчет итогов ---
            total_absorption_co2_eq = total_absorption_c * (-44/12)
            gwp_ch4 = 28; gwp_n2o = 265
            total_emission_co2_eq_from_ch4_n2o = (total_emission_ch4 * gwp_ch4) + (total_emission_n2o * gwp_n2o)
            total_emissions_co2_eq = total_emission_co2 + total_emission_co2_eq_from_ch4_n2o
            net_absorption_co2_eq = total_absorption_co2_eq + total_emissions_co2_eq # Поглощение < 0, Выброс > 0
            # --- Шаг 3: Отображение результата ---
            result = f"Сводный расчет поглощения (ПРИМЕРНЫЕ ДАННЫЕ):\n\n"
            result += f"Общее поглощение углерода (ΔC): {total_absorption_c:.4f} т C/год\n"
            result += f"-> Эквивалент поглощения CO2: {total_absorption_co2_eq:.4f} т CO2-экв/год\n\n"
            result += f"Выбросы от источников в секторе:\n"
            result += f"- Прямые выбросы CO2: {total_emission_co2:.4f} т CO2/год\n"
            result += f"- Выбросы CH4: {total_emission_ch4:.6f} т CH4/год (-> {total_emission_ch4 * gwp_ch4:.4f} т CO2-экв/год)\n"
            result += f"- Выбросы N2O: {total_emission_n2o:.6f} т N2O/год (-> {total_emission_n2o * gwp_n2o:.4f} т CO2-экв/год)\n"
            result += f"-> Суммарные выбросы: {total_emissions_co2_eq:.4f} т CO2-экв/год\n\n"
            result += f"ЧИСТОЕ ПОГЛОЩЕНИЕ (-)/ВЫБРОС (+): {net_absorption_co2_eq:.4f} т CO2-экв/год"
            self.result_text.setText(result)
            logging.info(f"AbsorptionSummaryTab: Summary calculated (dummy data): Net={net_absorption_co2_eq:.4f} t CO2eq/year")
        except Exception as e: handle_error(self, e, "AbsorptionSummaryTab", "Сводный расчет")