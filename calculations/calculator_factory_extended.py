# calculations/calculator_factory_extended.py
"""
Расширенная фабрика калькуляторов с поддержкой расчетов поглощения ПГ.
"""
from data_models_extended import DataService
from data_models_extended import ExtendedDataService

# Импорт существующих калькуляторов выбросов
from calculations.category_0 import Category0Calculator
from calculations.category_1 import Category1Calculator
from calculations.category_2 import Category2Calculator
from calculations.category_3 import Category3Calculator
from calculations.category_4 import Category4Calculator
from calculations.category_5 import Category5Calculator
from calculations.category_6 import Category6Calculator
from calculations.category_7 import Category7Calculator
from calculations.category_8 import Category8Calculator
from calculations.category_9 import Category9Calculator
from calculations.category_10 import Category10Calculator
from calculations.category_11 import Category11Calculator
from calculations.category_12 import Category12Calculator
from calculations.category_13 import Category13Calculator
from calculations.category_14 import Category14Calculator
from calculations.category_15 import Category15Calculator
from calculations.category_16 import Category16Calculator
from calculations.category_17 import Category17Calculator
from calculations.category_18 import Category18Calculator
from calculations.category_19 import Category19Calculator
from calculations.category_20 import Category20Calculator
from calculations.category_21 import Category21Calculator
from calculations.category_22 import Category22Calculator
from calculations.category_23 import Category23Calculator
from calculations.category_24 import Category24Calculator

# Импорт новых калькуляторов поглощения
from calculations.absorption_forest_restoration import (
    ForestRestorationCalculator,
    LandReclamationCalculator
)
from calculations.absorption_permanent_forest import (
    PermanentForestCalculator,
    ProtectiveForestCalculator
)
from calculations.absorption_agricultural import (
    AgriculturalLandCalculator,
    LandConversionCalculator
)


class ExtendedCalculatorFactory:
    """Расширенная фабрика для создания калькуляторов выбросов и поглощения ПГ."""
    
    def __init__(self):
        """Инициализация фабрики с обоими типами сервисов данных."""
        self._data_service = DataService()
        self._extended_data_service = ExtendedDataService()
        self._calculators = {}
        self._absorption_calculators = {}
        
    def get_calculator(self, category_name: str):
        """
        Возвращает калькулятор выбросов для указанной категории.
        Обратная совместимость с существующей системой.
        """
        if category_name not in self._calculators:
            calculator_class = self._get_emission_calculator_class(category_name)
            if calculator_class:
                if category_name == "Category0":
                    self._calculators[category_name] = calculator_class()
                else:
                    self._calculators[category_name] = calculator_class(self._data_service)
        return self._calculators.get(category_name)
    
    def get_absorption_calculator(self, calculator_type: str):
        """
        Возвращает калькулятор поглощения ПГ для указанного типа.
        
        :param calculator_type: Тип калькулятора поглощения
        :return: Экземпляр калькулятора поглощения
        """
        if calculator_type not in self._absorption_calculators:
            calculator_class = self._get_absorption_calculator_class(calculator_type)
            if calculator_class:
                # Калькуляторы поглощения используют расширенный сервис данных
                self._absorption_calculators[calculator_type] = calculator_class()
        return self._absorption_calculators.get(calculator_type)
    
    def _get_emission_calculator_class(self, category_name: str):
        """Получить класс калькулятора выбросов."""
        calculators_map = {
            "Category0": Category0Calculator,
            "Category1": Category1Calculator,
            "Category2": Category2Calculator,
            "Category3": Category3Calculator,
            "Category4": Category4Calculator,
            "Category5": Category5Calculator,
            "Category6": Category6Calculator,
            "Category7": Category7Calculator,
            "Category8": Category8Calculator,
            "Category9": Category9Calculator,
            "Category10": Category10Calculator,
            "Category11": Category11Calculator,
            "Category12": Category12Calculator,
            "Category13": Category13Calculator,
            "Category14": Category14Calculator,
            "Category15": Category15Calculator,
            "Category16": Category16Calculator,
            "Category17": Category17Calculator,
            "Category18": Category18Calculator,
            "Category19": Category19Calculator,
            "Category20": Category20Calculator,
            "Category21": Category21Calculator,
            "Category22": Category22Calculator,
            "Category23": Category23Calculator,
            "Category24": Category24Calculator,
        }
        return calculators_map.get(category_name)
    
    def _get_absorption_calculator_class(self, calculator_type: str):
        """Получить класс калькулятора поглощения."""
        absorption_map = {
            "ForestRestoration": ForestRestorationCalculator,
            "LandReclamation": LandReclamationCalculator,
            "PermanentForest": PermanentForestCalculator,
            "ProtectiveForest": ProtectiveForestCalculator,
            "AgriculturalLand": AgriculturalLandCalculator,
            "LandConversion": LandConversionCalculator,
        }
        return absorption_map.get(calculator_type)
    
    def get_extended_data_service(self) -> ExtendedDataService:
        """Получить расширенный сервис данных для прямого доступа к таблицам."""
        return self._extended_data_service


# ui/absorption_tabs.py
"""
UI вкладки для расчетов поглощения парниковых газов.
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QGroupBox,
    QTextEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.absorption_forest_restoration import ForestRestorationCalculator
from calculations.absorption_permanent_forest import PermanentForestCalculator
from calculations.absorption_agricultural import AgriculturalLandCalculator


class ForestRestorationTab(QWidget):
    """Вкладка для расчетов лесовосстановления (формулы 1-12)."""
    
    def __init__(self, calculator: ForestRestorationCalculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Группа для расчета изменения запасов углерода
        carbon_group = QGroupBox("Изменение запасов углерода (Формула 1)")
        carbon_layout = QFormLayout(carbon_group)
        
        self.biomass_input = self._create_line_edit((-1000, 1000, 2))
        carbon_layout.addRow("Изменение в биомассе (т C/год):", self.biomass_input)
        
        self.deadwood_input = self._create_line_edit((-1000, 1000, 2))
        carbon_layout.addRow("Изменение в мертвой древесине (т C/год):", self.deadwood_input)
        
        self.litter_input = self._create_line_edit((-1000, 1000, 2))
        carbon_layout.addRow("Изменение в подстилке (т C/год):", self.litter_input)
        
        self.soil_input = self._create_line_edit((-1000, 1000, 2))
        carbon_layout.addRow("Изменение в почве (т C/год):", self.soil_input)
        
        main_layout.addWidget(carbon_group)
        
        # Группа для расчета биомассы деревьев
        tree_group = QGroupBox("Расчет углерода в древостое (Формула 3)")
        tree_layout = QFormLayout(tree_group)
        
        self.tree_species = QComboBox()
        self.tree_species.addItems(["Ель", "Сосна", "Береза"])
        tree_layout.addRow("Порода дерева:", self.tree_species)
        
        self.tree_diameter = self._create_line_edit((0, 200, 1))
        tree_layout.addRow("Диаметр на высоте 1.3м (см):", self.tree_diameter)
        
        self.tree_height = self._create_line_edit((0, 100, 1))
        tree_layout.addRow("Высота дерева (м):", self.tree_height)
        
        self.tree_count = QSpinBox()
        self.tree_count.setRange(1, 10000)
        self.tree_count.setValue(1)
        tree_layout.addRow("Количество деревьев:", self.tree_count)
        
        main_layout.addWidget(tree_group)
        
        # Группа для выбросов от пожаров
        fire_group = QGroupBox("Выбросы от пожаров (Формула 6)")
        fire_layout = QFormLayout(fire_group)
        
        self.fire_area = self._create_line_edit((0, 100000, 2))
        fire_layout.addRow("Площадь пожара (га):", self.fire_area)
        
        self.fuel_mass = self._create_line_edit((0, 500, 2), "121.4")
        fire_layout.addRow("Масса топлива (т/га):", self.fuel_mass)
        
        self.combustion_factor = self._create_line_edit((0, 1, 3), "0.43")
        fire_layout.addRow("Коэффициент сгорания:", self.combustion_factor)
        
        self.gas_type = QComboBox()
        self.gas_type.addItems(["CO2", "CH4", "N2O"])
        fire_layout.addRow("Тип газа:", self.gas_type)
        
        main_layout.addWidget(fire_group)
        
        # Кнопки расчета
        button_layout = QHBoxLayout()
        
        self.calc_carbon_btn = QPushButton("Рассчитать изменение углерода")
        self.calc_carbon_btn.clicked.connect(self._calculate_carbon_change)
        button_layout.addWidget(self.calc_carbon_btn)
        
        self.calc_biomass_btn = QPushButton("Рассчитать углерод древостоя")
        self.calc_biomass_btn.clicked.connect(self._calculate_tree_biomass)
        button_layout.addWidget(self.calc_biomass_btn)
        
        self.calc_fire_btn = QPushButton("Рассчитать выбросы от пожара")
        self.calc_fire_btn.clicked.connect(self._calculate_fire_emissions)
        button_layout.addWidget(self.calc_fire_btn)
        
        main_layout.addLayout(button_layout)
        
        # Результаты
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(200)
        main_layout.addWidget(self.result_text)
        
    def _create_line_edit(self, validator_params, default_text="0"):
        line_edit = QLineEdit(default_text)
        validator = QDoubleValidator(*validator_params, self)
        validator.setLocale(self.c_locale)
        line_edit.setValidator(validator)
        return line_edit
    
    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(',', '.')
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)
    
    def _calculate_carbon_change(self):
        """Расчет изменения запасов углерода."""
        try:
            biomass = self._get_float(self.biomass_input, "Биомасса")
            deadwood = self._get_float(self.deadwood_input, "Мертвая древесина")
            litter = self._get_float(self.litter_input, "Подстилка")
            soil = self._get_float(self.soil_input, "Почва")
            
            total_change = self.calculator.calculate_carbon_stock_change(
                biomass, deadwood, litter, soil
            )
            
            # Перевод в CO2
            co2_equivalent = self.calculator.carbon_to_co2(total_change)
            
            result = f"Результаты расчета изменения запасов углерода:\n"
            result += f"Суммарное изменение: {total_change:.2f} т C/год\n"
            result += f"CO2-эквивалент: {co2_equivalent:.2f} т CO2/год\n"
            result += f"{'Поглощение' if total_change > 0 else 'Выброс'} парниковых газов"
            
            self.result_text.setText(result)
            
        except ValueError as e:
            self.result_text.setText(f"Ошибка: {e}")
        except Exception as e:
            self.result_text.setText(f"Непредвиденная ошибка: {e}")
            logging.error(f"Forest restoration calculation error: {e}", exc_info=True)
    
    def _calculate_tree_biomass(self):
        """Расчет углерода в биомассе деревьев."""
        try:
            from calculations.absorption_forest_restoration import ForestInventoryData
            
            species = self.tree_species.currentText().lower()
            diameter = self._get_float(self.tree_diameter, "Диаметр")
            height = self._get_float(self.tree_height, "Высота")
            count = self.tree_count.value()
            
            tree_data = ForestInventoryData(
                species=species,
                diameter=diameter,
                height=height,
                count=count
            )
            
            carbon = self.calculator.calculate_tree_biomass_carbon([tree_data])
            
            result = f"Результаты расчета углерода в древостое:\n"
            result += f"Порода: {species.capitalize()}\n"
            result += f"Параметры: D={diameter} см, H={height} м\n"
            result += f"Количество: {count} шт.\n"
            result += f"Углерод в биомассе: {carbon:.2f} кг C\n"
            result += f"Углерод на дерево: {carbon/count:.2f} кг C"
            
            self.result_text.setText(result)
            
        except Exception as e:
            self.result_text.setText(f"Ошибка расчета: {e}")
    
    def _calculate_fire_emissions(self):
        """Расчет выбросов от пожаров."""
        try:
            area = self._get_float(self.fire_area, "Площадь")
            fuel = self._get_float(self.fuel_mass, "Масса топлива")
            combustion = self._get_float(self.combustion_factor, "Коэффициент сгорания")
            gas = self.gas_type.currentText()
            
            emissions = self.calculator.calculate_fire_emissions(
                area, fuel, combustion, gas
            )
            
            # Если не CO2, пересчитываем в CO2-экв
            co2_eq = emissions
            if gas != 'CO2':
                co2_eq = self.calculator.to_co2_equivalent(emissions, gas)
            
            result = f"Результаты расчета выбросов от пожара:\n"
            result += f"Площадь пожара: {area:.2f} га\n"
            result += f"Тип пожара: {'Верховой' if combustion > 0.3 else 'Низовой'}\n"
            result += f"Выбросы {gas}: {emissions:.3f} т\n"
            if gas != 'CO2':
                result += f"CO2-эквивалент: {co2_eq:.3f} т CO2-экв"
            
            self.result_text.setText(result)
            
        except Exception as e:
            self.result_text.setText(f"Ошибка расчета: {e}")


class AgriculturalAbsorptionTab(QWidget):
    """Вкладка для расчетов поглощения ПГ сельхозугодьями."""
    
    def __init__(self, calculator: AgriculturalLandCalculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Создаем вкладки для разных типов расчетов
        tabs = QTabWidget()
        
        # Вкладка для минеральных почв
        mineral_tab = self._create_mineral_soil_tab()
        tabs.addTab(mineral_tab, "Минеральные почвы")
        
        # Вкладка для органогенных почв
        organic_tab = self._create_organic_soil_tab()
        tabs.addTab(organic_tab, "Органогенные почвы")
        
        # Вкладка для пожаров
        fire_tab = self._create_fire_tab()
        tabs.addTab(fire_tab, "Пожары")
        
        main_layout.addWidget(tabs)
        
        # Результаты
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(200)
        main_layout.addWidget(self.result_text)
    
    def _create_mineral_soil_tab(self):
        """Создание вкладки для расчетов по минеральным почвам."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Поступления углерода
        self.fert_carbon = self._create_line_edit((0, 10000, 2))
        layout.addRow("Углерод от удобрений (т C/год):", self.fert_carbon)
        
        self.lime_amount = self._create_line_edit((0, 10000, 2))
        layout.addRow("Количество извести (т/год):", self.lime_amount)
        
        self.plant_carbon = self._create_line_edit((0, 10000, 2))
        layout.addRow("Углерод от растений (т C/год):", self.plant_carbon)
        
        # Потери углерода
        self.resp_carbon = self._create_line_edit((0, 10000, 2))
        layout.addRow("Потери от дыхания (т C/год):", self.resp_carbon)
        
        self.erosion_area = self._create_line_edit((0, 100000, 2))
        layout.addRow("Площадь эрозии (га):", self.erosion_area)
        
        self.erosion_factor = self._create_line_edit((0, 10, 3), "0.5")
        layout.addRow("Коэффициент эрозии (т C/га/год):", self.erosion_factor)
        
        calc_btn = QPushButton("Рассчитать баланс углерода")
        calc_btn.clicked.connect(self._calculate_mineral_soil)
        layout.addRow(calc_btn)
        
        return widget
    
    def _create_organic_soil_tab(self):
        """Создание вкладки для расчетов по органогенным почвам."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.organic_area = self._create_line_edit((0, 100000, 2))
        layout.addRow("Площадь органогенных почв (га):", self.organic_area)
        
        self.gas_type_organic = QComboBox()
        self.gas_type_organic.addItems(["CO2", "N2O", "CH4"])
        layout.addRow("Тип газа:", self.gas_type_organic)
        
        calc_btn = QPushButton("Рассчитать выбросы")
        calc_btn.clicked.connect(self._calculate_organic_emissions)
        layout.addRow(calc_btn)
        
        return widget
    
    def _create_fire_tab(self):
        """Создание вкладки для расчетов выбросов от пожаров."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.agri_fire_area = self._create_line_edit((0, 100000, 2))
        layout.addRow("Площадь пожара (га):", self.agri_fire_area)
        
        self.agri_biomass = self._create_line_edit((0, 100, 2), "10.0")
        layout.addRow("Масса биомассы (т/га):", self.agri_biomass)
        
        self.agri_combustion = self._create_line_edit((0, 1, 3), "0.8")
        layout.addRow("Коэффициент сгорания:", self.agri_combustion)
        
        calc_btn = QPushButton("Рассчитать выбросы от пожара")
        calc_btn.clicked.connect(self._calculate_agri_fire)
        layout.addRow(calc_btn)
        
        return widget
    
    def _create_line_edit(self, validator_params, default_text="0"):
        line_edit = QLineEdit(default_text)
        validator = QDoubleValidator(*validator_params, self)
        validator.setLocale(self.c_locale)
        line_edit.setValidator(validator)
        return line_edit
    
    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(',', '.')
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)
    
    def _calculate_mineral_soil(self):
        """Расчет баланса углерода в минеральных почвах."""
        try:
            # Поступления
            fert = self._get_float(self.fert_carbon, "Углерод от удобрений")
            lime = self.calculator.calculate_lime_carbon(
                self._get_float(self.lime_amount, "Известь")
            )
            plant = self._get_float(self.plant_carbon, "Углерод от растений")
            
            # Потери
            resp = self._get_float(self.resp_carbon, "Дыхание")
            erosion = self.calculator.calculate_erosion_losses(
                self._get_float(self.erosion_area, "Площадь эрозии"),
                self._get_float(self.erosion_factor, "Коэффициент эрозии")
            )
            
            # Баланс
            balance = self.calculator.calculate_mineral_soil_carbon_change(
                fert, lime, plant, resp, erosion
            )
            
            result = f"Баланс углерода в минеральных почвах:\n"
            result += f"Поступления:\n"
            result += f"  - Удобрения: {fert:.2f} т C/год\n"
            result += f"  - Известь: {lime:.2f} т C/год\n"
            result += f"  - Растения: {plant:.2f} т C/год\n"
            result += f"Потери:\n"
            result += f"  - Дыхание: {resp:.2f} т C/год\n"
            result += f"  - Эрозия: {erosion:.2f} т C/год\n"
            result += f"БАЛАНС: {balance:.2f} т C/год\n"
            result += f"{'Накопление' if balance > 0 else 'Потеря'} углерода"
            
            self.result_text.setText(result)
            
        except Exception as e:
            self.result_text.setText(f"Ошибка: {e}")
    
    def _calculate_organic_emissions(self):
        """Расчет выбросов от органогенных почв."""
        try:
            area = self._get_float(self.organic_area, "Площадь")
            gas = self.gas_type_organic.currentText()
            
            if gas == "CO2":
                emissions = self.calculator.calculate_organic_soil_co2(area)
            elif gas == "N2O":
                emissions = self.calculator.calculate_organic_soil_n2o(area)
            else:  # CH4
                emissions = self.calculator.calculate_organic_soil_ch4(area) / 1000  # в тонны
            
            result = f"Выбросы от органогенных почв:\n"
            result += f"Площадь: {area:.2f} га\n"
            result += f"Выбросы {gas}: {emissions:.3f} т/год\n"
            
            if gas != "CO2":
                gwp = 25 if gas == "CH4" else 298
                co2_eq = emissions * gwp
                result += f"CO2-эквивалент: {co2_eq:.3f} т CO2-экв/год"
            
            self.result_text.setText(result)
            
        except Exception as e:
            self.result_text.setText(f"Ошибка: {e}")
    
    def _calculate_agri_fire(self):
        """Расчет выбросов от пожаров на сельхозземлях."""
        try:
            area = self._get_float(self.agri_fire_area, "Площадь")
            biomass = self._get_float(self.agri_biomass, "Биомасса")
            combustion = self._get_float(self.agri_combustion, "Сгорание")
            
            # Коэффициенты выбросов для сельхоз остатков
            emission_factors = {'CO2': 1515, 'CH4': 2.7, 'N2O': 0.07}
            
            result = f"Выбросы от пожара на сельхозземлях:\n"
            result += f"Площадь: {area:.2f} га\n"
            result += f"Масса биомассы: {biomass:.2f} т/га\n\n"
            
            total_co2_eq = 0
            for gas, ef in emission_factors.items():
                emissions = self.calculator.calculate_agricultural_fire_emissions(
                    area, biomass, combustion, ef
                )
                
                gwp = 1 if gas == 'CO2' else (25 if gas == 'CH4' else 298)
                co2_eq = emissions * gwp
                total_co2_eq += co2_eq
                
                result += f"{gas}: {emissions:.3f} т ({co2_eq:.3f} т CO2-экв)\n"
            
            result += f"\nОБЩИЕ выбросы: {total_co2_eq:.3f} т CO2-экв"
            
            self.result_text.setText(result)
            
        except Exception as e:
            self.result_text.setText(f"Ошибка: {e}")