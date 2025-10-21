# ui/absorption_tabs.py
"""
UI вкладки для расчетов поглощения парниковых газов.
"""
import logging
import math # Добавлен импорт math для LandReclamationTab
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QGroupBox,
    QTextEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QSpinBox, QDoubleSpinBox, QMessageBox, QScrollArea # Добавлен QScrollArea
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt, QLocale

# Импортируем соответствующие калькуляторы
from calculations.absorption_forest_restoration import ForestRestorationCalculator, ForestInventoryData, LandReclamationCalculator
from calculations.absorption_agricultural import AgriculturalLandCalculator, LandConversionCalculator, CropData, LivestockData # Добавлены CropData, LivestockData
from calculations.absorption_permanent_forest import PermanentForestCalculator, ProtectiveForestCalculator

# Добавляем импорт ExtendedDataService и ExtendedCalculatorFactory
from data_models_extended import ExtendedDataService
from calculations.calculator_factory_extended import ExtendedCalculatorFactory


# --- Вспомогательные функции и базовый класс (для уменьшения дублирования) ---

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

# --- Реализованные вкладки ---

class ForestRestorationTab(QWidget):
    """Вкладка для расчетов лесовосстановления (формулы 1-12)."""

    def __init__(self, calculator: ForestRestorationCalculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        # ... (Код UI для этой вкладки остается без изменений, как в предыдущих ответах) ...
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Группа для расчета изменения запасов углерода (Формула 1)
        carbon_group = QGroupBox("Общее изменение запасов углерода (Формула 1)")
        carbon_layout = QFormLayout(carbon_group)
        self.biomass_change_input = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Изменение углерода в живой биомассе за период, т C/год.")
        carbon_layout.addRow("ΔC биомасса (т C/год):", self.biomass_change_input)
        self.deadwood_change_input = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Изменение углерода в мертвой древесине за период, т C/год.")
        carbon_layout.addRow("ΔC мертвая древесина (т C/год):", self.deadwood_change_input)
        self.litter_change_input = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Изменение углерода в лесной подстилке за период, т C/год.")
        carbon_layout.addRow("ΔC подстилка (т C/год):", self.litter_change_input)
        self.soil_change_input = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Изменение углерода в почве за период, т C/год.")
        carbon_layout.addRow("ΔC почва (т C/год):", self.soil_change_input)
        main_layout.addWidget(carbon_group)
        # Группа для расчета биомассы деревьев (Формула 3)
        tree_group = QGroupBox("Углерод в биомассе древостоя (Формула 3)")
        tree_layout = QFormLayout(tree_group)
        self.tree_species = QComboBox()
        species_list = list(self.calculator.ALLOMETRIC_COEFFICIENTS.keys())
        self.tree_species.addItems([s.capitalize() for s in species_list])
        tree_layout.addRow("Порода дерева:", self.tree_species)
        self.tree_diameter = create_line_edit(self, validator_params=(0.1, 1000, 2), tooltip="Средний диаметр деревьев на высоте 1.3 м.")
        tree_layout.addRow("Диаметр (см):", self.tree_diameter)
        self.tree_height = create_line_edit(self, validator_params=(0.1, 100, 2), tooltip="Средняя высота деревьев.")
        tree_layout.addRow("Высота (м):", self.tree_height)
        self.tree_count = QSpinBox()
        self.tree_count.setRange(1, 1000000); self.tree_count.setValue(1)
        self.tree_count.setToolTip("Количество деревьев с указанными средними параметрами.")
        tree_layout.addRow("Количество деревьев:", self.tree_count)
        main_layout.addWidget(tree_group)
        # Группа для выбросов от пожаров (Формула 6)
        fire_group = QGroupBox("Выбросы от пожаров (Формула 6)")
        fire_layout = QFormLayout(fire_group)
        self.fire_area = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Площадь лесного пожара.")
        fire_layout.addRow("Площадь пожара (га):", self.fire_area)
        self.fire_fuel_mass = create_line_edit(self, "121.4", (0, 1000, 4), tooltip="Масса доступного для сгорания топлива. См. Таблицу 25.6.")
        fire_layout.addRow("Масса топлива (т/га):", self.fire_fuel_mass)
        self.fire_combustion_factor = create_line_edit(self, "0.43", (0.01, 1.0, 3), tooltip="Коэффициент сгорания (0.43 верховой, 0.15 низовой).")
        fire_layout.addRow("Коэффициент сгорания (доля):", self.fire_combustion_factor)
        self.fire_gas_type = QComboBox(); self.fire_gas_type.addItems(["CO2", "CH4", "N2O"])
        fire_layout.addRow("Тип газа:", self.fire_gas_type)
        main_layout.addWidget(fire_group)
        # Кнопки расчета
        button_layout = QHBoxLayout()
        self.calc_carbon_btn = QPushButton("Рассчитать ΔC общее"); self.calc_carbon_btn.clicked.connect(self._calculate_total_carbon_change)
        button_layout.addWidget(self.calc_carbon_btn)
        self.calc_biomass_btn = QPushButton("Рассчитать C древостоя"); self.calc_biomass_btn.clicked.connect(self._calculate_tree_biomass)
        button_layout.addWidget(self.calc_biomass_btn)
        self.calc_fire_btn = QPushButton("Рассчитать выбросы от пожара"); self.calc_fire_btn.clicked.connect(self._calculate_fire_emissions)
        button_layout.addWidget(self.calc_fire_btn)
        main_layout.addLayout(button_layout)
        # Результаты
        self.result_text = QTextEdit(); self.result_text.setReadOnly(True); self.result_text.setMaximumHeight(150)
        main_layout.addWidget(self.result_text)

    # --- Методы расчета для ForestRestorationTab ---
    def _calculate_total_carbon_change(self):
        try:
            biomass_change = get_float(self.biomass_change_input, "ΔC биомасса")
            deadwood_change = get_float(self.deadwood_change_input, "ΔC мертвая древесина")
            litter_change = get_float(self.litter_change_input, "ΔC подстилка")
            soil_change = get_float(self.soil_change_input, "ΔC почва")
            total_change = self.calculator.calculate_carbon_stock_change(biomass_change, deadwood_change, litter_change, soil_change)
            co2_equivalent = self.calculator.carbon_to_co2(total_change)
            result = (f"Общее изменение запасов углерода (Формула 1):\nΔC = {total_change:.4f} т C/год\nЭквивалент CO2: {co2_equivalent:.4f} т CO2/год\n({ 'Поглощение CO2' if co2_equivalent < 0 else 'Выброс CO2'})")
            self.result_text.setText(result)
            logging.info(f"ForestRestorationTab: Total carbon change calculated: {total_change:.4f} t C/year")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 1")

    def _calculate_tree_biomass(self):
        try:
            species = self.tree_species.currentText().lower()
            diameter = get_float(self.tree_diameter, "Диаметр")
            height = get_float(self.tree_height, "Высота")
            count = self.tree_count.value()
            tree_data = ForestInventoryData(species=species, diameter=diameter, height=height, count=count)
            carbon_kg = self.calculator.calculate_tree_biomass_carbon([tree_data], fraction="всего")
            carbon_tons = carbon_kg / 1000.0
            result = (f"Углерод в биомассе древостоя (Формула 3):\nПорода: {species.capitalize()}, D={diameter} см, H={height} м, Кол-во={count} шт.\nЗапас углерода: {carbon_tons:.6f} т C (или {carbon_kg:.3f} кг C)")
            self.result_text.setText(result)
            logging.info(f"ForestRestorationTab: Tree biomass carbon calculated: {carbon_tons:.6f} t C")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 3")

    def _calculate_fire_emissions(self):
        try:
            area = get_float(self.fire_area, "Площадь пожара")
            fuel_mass = get_float(self.fire_fuel_mass, "Масса топлива")
            combustion_factor = get_float(self.fire_combustion_factor, "Коэффициент сгорания")
            gas_type = self.fire_gas_type.currentText()
            emissions = self.calculator.calculate_fire_emissions(burned_area=area, available_fuel=fuel_mass, combustion_factor=combustion_factor, gas_type=gas_type)
            result = (f"Выбросы от пожара (Формула 6):\nПлощадь={area:.2f} га, Топливо={fuel_mass:.2f} т/га, К сгор.={combustion_factor:.3f}\nВыбросы {gas_type}: {emissions:.4f} т")
            if gas_type != "CO2":
                co2_eq = self.calculator.to_co2_equivalent(emissions, gas_type)
                result += f" (CO2-экв: {co2_eq:.4f} т)"
            self.result_text.setText(result)
            logging.info(f"ForestRestorationTab: Fire emissions calculated: {emissions:.4f} t {gas_type}")
        except Exception as e: handle_error(self, e, "ForestRestorationTab", "Ф. 6")


class AgriculturalAbsorptionTab(QWidget):
    """Вкладка для расчетов поглощения ПГ сельхозугодьями (формулы 75-90)."""

    def __init__(self, calculator: AgriculturalLandCalculator, data_service: ExtendedDataService, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.data_service = data_service
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        # ... (Код UI для этой вкладки остается без изменений, как в предыдущих ответах) ...
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
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
        return widget

    def _create_organic_soil_tab(self):
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
            result = f"ΔC в мин. почвах (Ф. 80): {delta_c:.4f} т C/год"; self.result_text.setText(result); logging.info(f"AgriTab: Mineral soil ΔC calculated: {delta_c:.4f} t C/year")
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
            result = f"ΔC биомассы (Ф. 77): {delta_c:.4f} т C/год"; self.result_text.setText(result); logging.info(f"AgriTab: Biomass ΔC calculated: {delta_c:.4f} t C/year")
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


# --- НОВЫЕ / ОБНОВЛЕННЫЕ ВКЛАДКИ ---

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
        outer_layout = QVBoxLayout(self); outer_layout.addWidget(scroll_area) # Layout для самой вкладки

        # --- Блок Биомасса (Ф. 27-35) ---
        biomass_group = QGroupBox("Расчеты по биомассе (Формулы 27-35)")
        biomass_layout = QVBoxLayout(biomass_group)

        # Ф. 27: Запас углерода в биомассе
        layout_f27 = QFormLayout()
        self.f27_volume = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас древесины, м³/га")
        self.f27_conversion_factor = create_line_edit(self, validator_params=(0, 10, 4), tooltip="Коэффициент перевода KP_ij")
        layout_f27.addRow("Запас древесины (V_ij, м³/га):", self.f27_volume)
        layout_f27.addRow("Коэф. перевода биомассы (KP_ij):", self.f27_conversion_factor)
        calc_f27_btn = QPushButton("Рассчитать C биомассы (Ф. 27)"); calc_f27_btn.clicked.connect(self._calculate_f27)
        layout_f27.addRow(calc_f27_btn)
        biomass_layout.addLayout(layout_f27)

        # Ф. 28: Средний запас углерода на гектар
        layout_f28 = QFormLayout()
        self.f28_carbon_stock = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас углерода, т C (из Ф.27 или др.)")
        self.f28_area = create_line_edit(self, validator_params=(0.001, 1e12, 4), tooltip="Площадь участка, га")
        layout_f28.addRow("Запас углерода (CP_ij, т C):", self.f28_carbon_stock)
        layout_f28.addRow("Площадь (S_ij, га):", self.f28_area)
        calc_f28_btn = QPushButton("Рассчитать средний C/га (Ф. 28)"); calc_f28_btn.clicked.connect(self._calculate_f28)
        layout_f28.addRow(calc_f28_btn)
        biomass_layout.addLayout(layout_f28)

        # Ф. 35: Годичный бюджет углерода биомассы
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

        # --- Блок Почва (Ф. 49-54) ---
        soil_group = QGroupBox("Расчеты по почве (Формулы 49-54)")
        soil_layout = QVBoxLayout(soil_group)
        # Добавьте сюда поля для Ф.49, Ф.50, Ф.52, Ф.53 и кнопку для Ф.54
        # ... (пропущено для краткости)
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

        # Ф. 56: CO2 от осушения
        layout_f56 = QFormLayout()
        self.f56_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь осушенных лесных почв, га")
        self.f56_ef = create_line_edit(self, "0.71", (0, 100, 4), tooltip="Коэффициент выброса, т C/га/год")
        layout_f56.addRow("Площадь осушения (A, га):", self.f56_area)
        layout_f56.addRow("Коэф. выброса CO2 (EF, т C/га/год):", self.f56_ef)
        calc_f56_btn = QPushButton("Рассчитать CO2 от осушения (Ф. 56)"); calc_f56_btn.clicked.connect(self._calculate_f56)
        layout_f56.addRow(calc_f56_btn)
        emissions_layout.addLayout(layout_f56)

        # Ф. 59: Выбросы от пожаров
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

        # Добавьте сюда поля для Ф.57 (N2O) и Ф.58 (CH4) от осушения...

        main_layout.addWidget(emissions_group)

        # --- Результаты ---
        self.result_text = QTextEdit("Здесь будут результаты расчетов...")
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(200) # Увеличим немного
        main_layout.addWidget(self.result_text)

    # --- Методы расчета для PermanentForestTab ---
    def _calculate_f27(self):
        try:
            volume = get_float(self.f27_volume, "Запас древесины (Ф.27)")
            factor = get_float(self.f27_conversion_factor, "Коэф. перевода (Ф.27)")
            carbon_stock = self.calculator.calculate_biomass_carbon_stock(volume, factor)
            self.result_text.setText(f"Запас углерода (Ф. 27): {carbon_stock:.4f} т C") # т C, а не т C/га
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
            self.result_text.setText(f"Бюджет биомассы (Ф. 35): {budget:.4f} т C/год")
            logging.info(f"PermanentForestTab: F35 calculated: {budget:.4f} t C/year")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 35")

    def _calculate_f55(self):
        try:
            bp = get_float(self.f55_biomass_budget, "Бюджет биомассы (Ф.55)")
            bd = get_float(self.f55_deadwood_budget, "Бюджет мертв.древ. (Ф.55)")
            bl = get_float(self.f55_litter_budget, "Бюджет подстилки (Ф.55)")
            bs = get_float(self.f55_soil_budget, "Бюджет почвы (Ф.55)")
            total_budget = self.calculator.calculate_total_budget(bp, bd, bl, bs)
            # Переводим в CO2 эквивалент
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
            area = get_float(self.f56_area, "Площадь осушения (Ф.56)")
            ef = get_float(self.f56_ef, "Коэф. выброса (Ф.56)")
            co2_emission = self.calculator.calculate_drained_forest_co2(area, ef)
            self.result_text.setText(f"Выбросы CO2 от осушения (Ф. 56): {co2_emission:.4f} т CO2/год")
            logging.info(f"PermanentForestTab: F56 calculated: {co2_emission:.4f} t CO2/year")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 56")

    def _calculate_f59(self):
        try:
            area = get_float(self.f59_area, "Площадь пожара (Ф.59)")
            fuel_mass = get_float(self.f59_fuel_mass, "Масса топлива (Ф.59)")
            comb_factor = get_float(self.f59_comb_factor, "Коэф. сгорания (Ф.59)")
            gas_type = self.f59_gas_type.currentText()
            # Получаем EF_gas из data_service (для лесов)
            ef_value = self.data_service.get_fire_emission_factor('леса', gas_type)
            if ef_value is None: raise ValueError(f"Коэффициент выброса для {gas_type} (леса) не найден.")

            emission = self.calculator.calculate_forest_fire_emissions(area, fuel_mass, comb_factor, ef_value)

            result = (f"Выбросы от пожара (Ф. 59):\n"
                      f"Площадь={area:.2f} га, Топливо={fuel_mass:.2f} т/га, К сгор.={comb_factor:.3f}\n"
                      f"Выбросы {gas_type}: {emission:.4f} т")
            # Добавляем CO2-эквивалент
            gwp_factors = {"CO2": 1, "CH4": 28, "N2O": 265}
            gwp = gwp_factors.get(gas_type, 1)
            if gwp != 1:
                co2_eq = emission * gwp
                result += f" (CO2-экв: {co2_eq:.4f} т)"
            self.result_text.setText(result)
            logging.info(f"PermanentForestTab: F59 calculated: {emission:.4f} t {gas_type}")
        except Exception as e: handle_error(self, e, "PermanentForestTab", "Ф. 59")


class ProtectiveForestTab(QWidget):
    """Вкладка для расчетов по защитным насаждениям (Формулы 60-74)."""
    def __init__(self, calculator: ProtectiveForestCalculator, data_service: ExtendedDataService, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.data_service = data_service
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()
        logging.info("ProtectiveForestTab initialized.")

    def _init_ui(self):
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget); main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(main_widget)
        outer_layout = QVBoxLayout(self); outer_layout.addWidget(scroll_area)

        # --- Динамика запасов по годам (Ф. 60, 63, 66, 69) ---
        dynamics_group = QGroupBox("Динамика запасов углерода (Формулы 60, 63, 66, 69)")
        dynamics_layout = QVBoxLayout(dynamics_group)
        # Пример для Ф.60
        layout_f60 = QFormLayout()
        self.f60_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь насаждений определенного года создания, га")
        self.f60_mean_carbon = create_line_edit(self, validator_params=(0, 1000, 4), tooltip="Средний запас углерода в БИОМАССЕ для данного возраста, т C/га")
        layout_f60.addRow("Площадь насаждений (SA_j1, га):", self.f60_area)
        layout_f60.addRow("Средний запас C биомассы (CPAM_ij, т C/га):", self.f60_mean_carbon)
        calc_f60_btn = QPushButton("Рассчитать запас C биомассы (Ф. 60)"); calc_f60_btn.clicked.connect(self._calculate_f60)
        layout_f60.addRow(calc_f60_btn)
        dynamics_layout.addLayout(layout_f60)
        # Добавьте сюда поля и кнопки для Ф. 63 (мертв. орг. вещ.), Ф. 66 (подстилка), Ф. 69 (почва)...
        main_layout.addWidget(dynamics_group)

        # --- Годичное накопление (Ф. 62, 65, 68, 71) ---
        accum_group = QGroupBox("Годичное накопление углерода (Формулы 62, 65, 68, 71)")
        accum_layout = QVBoxLayout(accum_group)
        # Пример для Ф.62
        layout_f62 = QFormLayout()
        self.f62_carbon_next = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Суммарный запас C в биомассе в СЛЕДУЮЩЕМ году, т C (из Ф.61)")
        self.f62_carbon_current = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Суммарный запас C в биомассе в ТЕКУЩЕМ году, т C (из Ф.61)")
        layout_f62.addRow("Запас C биомассы (i+1) (т C):", self.f62_carbon_next)
        layout_f62.addRow("Запас C биомассы (i) (т C):", self.f62_carbon_current)
        calc_f62_btn = QPushButton("Рассчитать накопление C биомассы (Ф. 62)"); calc_f62_btn.clicked.connect(self._calculate_f62)
        layout_f62.addRow(calc_f62_btn)
        accum_layout.addLayout(layout_f62)
        # Добавьте сюда поля и кнопки для Ф. 65, 68, 71...
        main_layout.addWidget(accum_group)

        # --- Общее накопление (Ф. 72) ---
        total_accum_group = QGroupBox("Общее накопление углерода (Формула 72)")
        layout_f72 = QFormLayout(total_accum_group)
        self.f72_biomass_acc = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Накопление в биомассе, т C/год (из Ф.62)")
        self.f72_deadwood_acc = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Накопление в мертв. орг. вещ., т C/год (из Ф.65)")
        self.f72_litter_acc = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Накопление в подстилке, т C/год (из Ф.68)")
        self.f72_soil_acc = create_line_edit(self, validator_params=(-1e9, 1e9, 4), tooltip="Накопление в почве, т C/год (из Ф.71)")
        layout_f72.addRow("Накопление биомасса (CPAS, т C/год):", self.f72_biomass_acc)
        layout_f72.addRow("Накопление мертв.орг. (CPDS, т C/год):", self.f72_deadwood_acc)
        layout_f72.addRow("Накопление подстилка (CPLS, т C/год):", self.f72_litter_acc)
        layout_f72.addRow("Накопление почва (CPSS, т C/год):", self.f72_soil_acc)
        calc_f72_btn = QPushButton("Рассчитать общее накопление (Ф. 72)"); calc_f72_btn.clicked.connect(self._calculate_f72)
        layout_f72.addRow(calc_f72_btn)
        main_layout.addWidget(total_accum_group)

        # --- Выбросы от осушения (Ф. 73, 74) ---
        drain_group = QGroupBox("Выбросы от осушения переведенных земель (Формулы 73, 74)")
        # Добавьте сюда поля и кнопки для Ф. 73 (CO2) и Ф. 74 (N2O)...
        main_layout.addWidget(drain_group)

        # --- Результаты ---
        self.result_text = QTextEdit("Здесь будут результаты расчетов...")
        self.result_text.setReadOnly(True); self.result_text.setMaximumHeight(150)
        main_layout.addWidget(self.result_text)

    # --- Методы расчета для ProtectiveForestTab ---
    def _calculate_f60(self):
        try:
            area = get_float(self.f60_area, "Площадь (Ф.60)")
            mean_carbon = get_float(self.f60_mean_carbon, "Средний запас C (Ф.60)")
            total_carbon = self.calculator.calculate_protective_biomass_dynamics(area, mean_carbon)
            self.result_text.setText(f"Запас C в биомассе для года {1} (Ф. 60): {total_carbon:.4f} т C")
            logging.info(f"ProtectiveForestTab: F60 calculated: {total_carbon:.4f} t C")
        except Exception as e: handle_error(self, e, "ProtectiveForestTab", "Ф. 60")

    def _calculate_f62(self):
        try:
            c_next = get_float(self.f62_carbon_next, "Запас C (i+1) (Ф.62)")
            c_current = get_float(self.f62_carbon_current, "Запас C (i) (Ф.62)")
            accumulation = self.calculator.calculate_protective_biomass_absorption(c_next, c_current)
            self.result_text.setText(f"Накопление C в биомассе (Ф. 62): {accumulation:.4f} т C/год")
            logging.info(f"ProtectiveForestTab: F62 calculated: {accumulation:.4f} t C/year")
        except Exception as e: handle_error(self, e, "ProtectiveForestTab", "Ф. 62")

    def _calculate_f72(self):
        try:
            acc_b = get_float(self.f72_biomass_acc, "Накопление биомасса (Ф.72)")
            acc_d = get_float(self.f72_deadwood_acc, "Накопление мертв.орг. (Ф.72)")
            acc_l = get_float(self.f72_litter_acc, "Накопление подстилка (Ф.72)")
            acc_s = get_float(self.f72_soil_acc, "Накопление почва (Ф.72)")
            total_acc = self.calculator.calculate_protective_total_accumulation(acc_b, acc_d, acc_l, acc_s)
            co2_eq = total_acc * (-44/12)
            result = (f"Общее накопление (Ф. 72):\n"
                      f"CPS = {total_acc:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год\n"
                      f"({ 'Поглощение CO2' if co2_eq < 0 else 'Выброс CO2'})")
            self.result_text.setText(result)
            logging.info(f"ProtectiveForestTab: F72 calculated: {total_acc:.4f} t C/year")
        except Exception as e: handle_error(self, e, "ProtectiveForestTab", "Ф. 72")

    # Добавьте сюда другие _calculate_fXX методы


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

        # Ф. 14/15 - общие параметры
        params_layout = QFormLayout()
        self.f14_15_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь рекультивации, га")
        self.f14_15_period = create_line_edit(self, "1", (0.1, 100, 2), tooltip="Период между измерениями запасов, лет")
        params_layout.addRow("Площадь (A_рек, га):", self.f14_15_area)
        params_layout.addRow("Период (D, лет):", self.f14_15_period)
        change_layout.addLayout(params_layout)

        # Ф. 14: Изменение в биомассе
        layout_f14 = QFormLayout()
        self.f14_c_after = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас C в биомассе ПОСЛЕ рекультивации, т C/га")
        self.f14_c_before = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас C в биомассе ДО рекультивации, т C/га")
        layout_f14.addRow("C биомассы ПОСЛЕ (т C/га):", self.f14_c_after)
        layout_f14.addRow("C биомассы ДО (т C/га):", self.f14_c_before)
        calc_f14_btn = QPushButton("Рассчитать ΔC биомассы (Ф. 14)"); calc_f14_btn.clicked.connect(self._calculate_f14)
        layout_f14.addRow(calc_f14_btn)
        change_layout.addLayout(layout_f14)

        # Ф. 15: Изменение в почве
        layout_f15 = QFormLayout()
        self.f15_soil_after = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас C в почве ПОСЛЕ рекультивации, т C/га")
        self.f15_soil_before = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Запас C в почве ДО рекультивации, т C/га")
        layout_f15.addRow("C почвы ПОСЛЕ (т C/га):", self.f15_soil_after)
        layout_f15.addRow("C почвы ДО (т C/га):", self.f15_soil_before)
        calc_f15_btn = QPushButton("Рассчитать ΔC почвы (Ф. 15)"); calc_f15_btn.clicked.connect(self._calculate_f15)
        layout_f15.addRow(calc_f15_btn)
        change_layout.addLayout(layout_f15)

        # Ф. 13: Суммарное изменение
        layout_f13 = QFormLayout()
        self.f13_biomass_change_res = QLineEdit(); self.f13_biomass_change_res.setReadOnly(True); self.f13_biomass_change_res.setPlaceholderText("Результат Ф.14")
        self.f13_soil_change_res = QLineEdit(); self.f13_soil_change_res.setReadOnly(True); self.f13_soil_change_res.setPlaceholderText("Результат Ф.15")
        layout_f13.addRow("ΔC биомасса (т C/год):", self.f13_biomass_change_res)
        layout_f13.addRow("ΔC почва (т C/год):", self.f13_soil_change_res)
        calc_f13_btn = QPushButton("Рассчитать ΔC конверсии (Ф. 13)"); calc_f13_btn.clicked.connect(self._calculate_f13)
        layout_f13.addRow(calc_f13_btn)
        change_layout.addLayout(layout_f13)

        main_layout.addWidget(change_group)

        # --- Углерод в травянистой биомассе (Ф. 20-22) ---
        grass_group = QGroupBox("Углерод в травянистой биомассе (Формулы 20-22)")
        grass_layout = QVBoxLayout(grass_group)
        # Ф. 21
        layout_f21 = QFormLayout()
        self.f21_dry_weight = create_line_edit(self, validator_params=(0, 1e6, 4), tooltip="Абсолютно сухой вес пробы травы с площадки 0.04 га, кг")
        layout_f21.addRow("Сухой вес пробы (кг):", self.f21_dry_weight)
        calc_f21_btn = QPushButton("Рассчитать C надземной биомассы (Ф. 21)"); calc_f21_btn.clicked.connect(self._calculate_f21)
        layout_f21.addRow(calc_f21_btn)
        grass_layout.addLayout(layout_f21)
        # Добавьте сюда поля для Ф. 22 и кнопку для Ф. 20...
        main_layout.addWidget(grass_group)

        # --- Углерод в почве (Ф. 23) ---
        soil_c_group = QGroupBox("Запас углерода в почве (Формула 23 / 5)")
        layout_f23 = QFormLayout(soil_c_group)
        self.f23_org_percent = create_line_edit(self, validator_params=(0, 100, 4), tooltip="Содержание органического вещества, %")
        self.f23_depth_cm = create_line_edit(self, "30", (1, 200, 2), tooltip="Глубина отбора проб, см")
        self.f23_bulk_density = create_line_edit(self, validator_params=(0.1, 5, 4), tooltip="Объемная масса почвы, г/см³")
        layout_f23.addRow("Орг. вещество (%):", self.f23_org_percent)
        layout_f23.addRow("Глубина (см):", self.f23_depth_cm)
        layout_f23.addRow("Объемная масса (г/см³):", self.f23_bulk_density)
        calc_f23_btn = QPushButton("Рассчитать запас C в почве (Ф. 23)"); calc_f23_btn.clicked.connect(self._calculate_f23)
        layout_f23.addRow(calc_f23_btn)
        main_layout.addWidget(soil_c_group)

        # Добавьте сюда группы для Ф. 24 (топливо), Ф. 25/26 (перевод в CO2)...

        # --- Результаты ---
        self.result_text = QTextEdit("Здесь будут результаты расчетов...")
        self.result_text.setReadOnly(True); self.result_text.setMaximumHeight(150)
        main_layout.addWidget(self.result_text)

    # --- Методы расчета для LandReclamationTab ---
    def _calculate_f14(self):
        try:
            c_after = get_float(self.f14_c_after, "C биомассы ПОСЛЕ (Ф.14)")
            c_before = get_float(self.f14_c_before, "C биомассы ДО (Ф.14)")
            area = get_float(self.f14_15_area, "Площадь (Ф.14)")
            period = get_float(self.f14_15_period, "Период (Ф.14)")
            delta_c = self.calculator.calculate_reclamation_biomass_change(c_after, c_before, area, period)
            self.f13_biomass_change_res.setText(f"{delta_c:.4f}") # Помещаем результат в поле для Ф.13
            self.result_text.setText(f"ΔC биомассы (Ф. 14): {delta_c:.4f} т C/год")
            logging.info(f"LandReclamationTab: F14 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 14")

    def _calculate_f15(self):
        try:
            soil_after = get_float(self.f15_soil_after, "C почвы ПОСЛЕ (Ф.15)")
            soil_before = get_float(self.f15_soil_before, "C почвы ДО (Ф.15)")
            area = get_float(self.f14_15_area, "Площадь (Ф.15)")
            period = get_float(self.f14_15_period, "Период (Ф.15)")
            delta_c = self.calculator.calculate_reclamation_soil_change(soil_after, soil_before, area, period)
            self.f13_soil_change_res.setText(f"{delta_c:.4f}") # Помещаем результат в поле для Ф.13
            self.result_text.setText(f"ΔC почвы (Ф. 15): {delta_c:.4f} т C/год")
            logging.info(f"LandReclamationTab: F15 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 15")

    def _calculate_f13(self):
        try:
            # Берем результаты из полей, заполненных расчетами Ф.14 и Ф.15
            biomass_change = get_float(self.f13_biomass_change_res, "ΔC биомасса (из Ф.14)")
            soil_change = get_float(self.f13_soil_change_res, "ΔC почва (из Ф.15)")
            delta_c = self.calculator.calculate_conversion_carbon_change(biomass_change, soil_change)
            co2_eq = delta_c * (-44/12)
            result = (f"ΔC конверсии (Ф. 13):\n"
                      f"ΔC = {delta_c:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год\n"
                      f"({ 'Поглощение CO2' if co2_eq < 0 else 'Выброс CO2'})")
            self.result_text.setText(result)
            logging.info(f"LandReclamationTab: F13 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 13")

    def _calculate_f21(self):
        try:
            dry_weight = get_float(self.f21_dry_weight, "Сухой вес пробы (Ф.21)")
            # area_correction используется по умолчанию в калькуляторе
            carbon = self.calculator.calculate_aboveground_grass_carbon(dry_weight)
            self.result_text.setText(f"C надземной трав. биомассы (Ф. 21): {carbon:.4f} т C/га")
            logging.info(f"LandReclamationTab: F21 calculated: {carbon:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 21")

    def _calculate_f23(self):
        try:
            org_perc = get_float(self.f23_org_percent, "Орг. вещество (Ф.23)")
            depth = get_float(self.f23_depth_cm, "Глубина (Ф.23)")
            density = get_float(self.f23_bulk_density, "Объемная масса (Ф.23)")
            carbon_stock = self.calculator.calculate_soil_carbon_from_organic(org_perc, depth, density)
            self.result_text.setText(f"Запас C в почве (Ф. 23): {carbon_stock:.4f} т C/га")
            logging.info(f"LandReclamationTab: F23 calculated: {carbon_stock:.4f} t C/ha")
        except Exception as e: handle_error(self, e, "LandReclamationTab", "Ф. 23")

    # Добавьте сюда другие _calculate_fXX методы


class LandConversionTab(QWidget):
    """Вкладка для расчетов по конверсии земель (Формулы 91-100)."""
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
        self.f91_c_after = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Суммарный запас C ПОСЛЕ конверсии (все пулы), т C/га")
        self.f91_c_before = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Суммарный запас C ДО конверсии (все пулы), т C/га")
        self.f91_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь конверсии, га")
        self.f91_period = create_line_edit(self, "20", (1, 100, 1), tooltip="Период конверсии, лет (стандартно 20)")
        layout_f91.addRow("C после (т C/га):", self.f91_c_after)
        layout_f91.addRow("C до (т C/га):", self.f91_c_before)
        layout_f91.addRow("Площадь конверсии (ΔA, га):", self.f91_area)
        layout_f91.addRow("Период конверсии (D, лет):", self.f91_period)
        calc_f91_btn = QPushButton("Рассчитать ΔC конверсии (Ф. 91)"); calc_f91_btn.clicked.connect(self._calculate_f91)
        layout_f91.addRow(calc_f91_btn)
        main_layout.addWidget(group_f91)

        # --- Изменение C в почвах корм. угодий (Ф. 96) ---
        group_f96 = QGroupBox("Изменение C в почвах кормовых угодий (Формула 96)")
        layout_f96 = QFormLayout(group_f96)
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
        main_layout.addWidget(group_f96)

        # --- Вынос C с сеном (Ф. 100) ---
        group_f100 = QGroupBox("Вынос углерода с сеном (Формула 100)")
        layout_f100 = QFormLayout(group_f100)
        self.f100_hay_yield = create_line_edit(self, validator_params=(0, 1e9, 4), tooltip="Годовая урожайность сена, т/год")
        layout_f100.addRow("Урожайность сена (Yhay, т/год):", self.f100_hay_yield)
        calc_f100_btn = QPushButton("Рассчитать вынос C (Ф. 100) -> подставить в Ф.96")
        calc_f100_btn.clicked.connect(self._calculate_f100)
        layout_f100.addRow(calc_f100_btn)
        main_layout.addWidget(group_f100)

        # Добавьте сюда группы и поля для Ф. 92-95 (выбросы от осушения/пожаров), Ф. 97-99 ...

        # --- Результаты ---
        self.result_text = QTextEdit("Здесь будут результаты расчетов...")
        self.result_text.setReadOnly(True); self.result_text.setMaximumHeight(150)
        main_layout.addWidget(self.result_text)

    # --- Методы расчета для LandConversionTab ---
    def _calculate_f91(self):
        try:
            # Для упрощения примера предполагаем, что C_после и C_до - это суммы по всем категориям
            # В реальном UI может потребоваться ввод по категориям или использование табличных данных
            c_after_list = [get_float(self.f91_c_after, "C после (Ф.91)")]
            c_before_list = [get_float(self.f91_c_before, "C до (Ф.91)")]
            area = get_float(self.f91_area, "Площадь конверсии (Ф.91)")
            period = get_float(self.f91_period, "Период конверсии (Ф.91)")
            delta_c = self.calculator.calculate_conversion_carbon_change(c_after_list, c_before_list, area, period)
            co2_eq = delta_c * (-44/12)
            result = (f"ΔC конверсии (Ф. 91):\n"
                      f"ΔC = {delta_c:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год\n"
                      f"({ 'Поглощение CO2' if co2_eq < 0 else 'Выброс CO2'})")
            self.result_text.setText(result)
            logging.info(f"LandConversionTab: F91 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 91")

    def _calculate_f96(self):
        try:
            plant = get_float(self.f96_c_plant, "C растения (Ф.96)")
            manure = get_float(self.f96_c_manure, "C навоз (Ф.96)")
            resp = get_float(self.f96_c_resp, "C дыхание (Ф.96)")
            erosion = get_float(self.f96_c_erosion, "C эрозия (Ф.96)")
            hay = get_float(self.f96_c_hay, "C сено (Ф.96)")
            feed = get_float(self.f96_c_feed, "C корм (Ф.96)")
            green = get_float(self.f96_c_green, "C зел. масса (Ф.96)")
            delta_c = self.calculator.calculate_grassland_soil_carbon_change(plant, manure, resp, erosion, hay, feed, green)
            self.result_text.setText(f"ΔC почв корм. угодий (Ф. 96): {delta_c:.4f} т C/год")
            logging.info(f"LandConversionTab: F96 calculated: {delta_c:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 96")

    def _calculate_f100(self):
        try:
            hay_yield = get_float(self.f100_hay_yield, "Урожайность сена (Ф.100)")
            carbon_removal = self.calculator.calculate_hay_carbon_removal(hay_yield)
            # Подставляем результат в поле для Ф.96
            self.f96_c_hay.setText(self.c_locale.toString(carbon_removal, 'f', 4))
            self.result_text.setText(f"Вынос углерода с сеном (Ф. 100): {carbon_removal:.4f} т C/год (значение подставлено в Ф.96)")
            logging.info(f"LandConversionTab: F100 calculated: {carbon_removal:.4f} t C/year")
        except Exception as e: handle_error(self, e, "LandConversionTab", "Ф. 100")

    # Добавьте сюда другие _calculate_fXX методы


class AbsorptionSummaryTab(QWidget):
    """Вкладка для сводного расчета поглощения."""
    def __init__(self, factory: ExtendedCalculatorFactory, parent=None):
        super().__init__(parent)
        self.factory = factory
        self._init_ui()
        logging.info("AbsorptionSummaryTab initialized.")

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        label = QLabel("Сводный расчет поглощения")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(label)

        self.summary_button = QPushButton("Собрать данные и рассчитать итог")
        self.summary_button.clicked.connect(self._calculate_summary)
        main_layout.addWidget(self.summary_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.result_text = QTextEdit("Нажмите кнопку для расчета сводного поглощения...\n(Функционал сбора данных не реализован)")
        self.result_text.setReadOnly(True)
        main_layout.addWidget(self.result_text)

    def _calculate_summary(self):
        # !! ВНИМАНИЕ: Эта функция - только примерная структура !!
        # Требуется доработка логики сбора данных из других вкладок.
        try:
            logging.info("Calculating absorption summary...")
            total_absorption_c = 0.0 # Суммарное поглощение углерода
            total_emission_co2 = 0.0 # Суммарные прямые выбросы CO2 из сектора
            total_emission_ch4 = 0.0 # Суммарные выбросы CH4 из сектора
            total_emission_n2o = 0.0 # Суммарные выбросы N2O из сектора

            # --- Шаг 1: Сбор данных из других вкладок ---
            # Это самая сложная часть. Нужно получить РЕЗУЛЬТАТЫ расчетов
            # из каждой вкладки поглощения.
            # Возможные подходы:
            # 1. Парсить текст из self.tabs_widget.widget(i).result_text.toPlainText()
            #    (ненадежно, зависит от формата текста)
            # 2. Добавить во все вкладки метод get_latest_results(), который
            #    возвращает словарь с последними рассчитанными значениями.
            # 3. Использовать сигналы/слоты или общую модель данных (более правильно, но сложнее).

            # --- ПРИМЕР (НЕ РАБОТАЕТ БЕЗ ЛОГИКИ СБОРА): ---
            # delta_c_forest_restoration = self._parse_delta_c(self.factory.parent_window.absorption_tabs.widget(0)) # Индекс вкладки
            # delta_c_permanent_forest = self._parse_delta_c(self.factory.parent_window.absorption_tabs.widget(1))
            # ... и т.д.
            # emissions_co2_permanent_forest = self._parse_emissions(self.factory.parent_window.absorption_tabs.widget(1), "CO2")
            # emissions_ch4_agricultural = self._parse_emissions(self.factory.parent_window.absorption_tabs.widget(3), "CH4")
            # ... и т.д.
            # total_absorption_c = delta_c_forest_restoration + delta_c_permanent_forest + ...
            # total_emission_co2 = emissions_co2_permanent_forest + ...
            # total_emission_ch4 = emissions_ch4_agricultural + ...
            # total_emission_n2o = ...

            # Пока используем заглушки
            total_absorption_c = 100.0 # Пример
            total_emission_co2 = 5.0   # Пример
            total_emission_ch4 = 0.2   # Пример
            total_emission_n2o = 0.05  # Пример
            QMessageBox.warning(self, "Внимание", "Расчет выполнен с примерными данными.\nФункционал сбора данных со вкладок не реализован.")


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

        except Exception as e:
            handle_error(self, e, "AbsorptionSummaryTab", "Сводный расчет")

    # Добавьте сюда методы для парсинга результатов, если выберете этот подход
    # def _parse_delta_c(self, tab_widget): ...
    # def _parse_emissions(self, tab_widget, gas_type): ...