# calculations/absorption_forest_restoration.py
"""
Калькуляторы для расчета поглощения парниковых газов при лесовосстановлении.
Формулы 1-26 из Приказа Минприроды РФ от 27.05.2022 N 371.

ИСПРАВЛЕНИЯ:
- Обновлены значения GWP на актуальные AR5 IPCC (2014): CH4=28, N2O=265
- Уточнены формулы перевода углерода в CO2
- Используются централизованные константы из config.py и gwp_constants.py
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math

from config import CARBON_TO_CO2_FACTOR, N2O_N_TO_N2O_FACTOR
from calculations.gwp_constants import GWP_AR5_100Y


@dataclass
class ForestInventoryData:
    """Данные учета древостоя."""

    species: str  # Порода дерева
    diameter: float  # Диаметр на высоте 1.3м, см
    height: float  # Высота, м
    count: int = 1  # Количество деревьев


class ForestRestorationCalculator:
    """Калькулятор поглощения ПГ при лесовосстановлении (формулы 1-12)."""

    # Используем централизованные значения GWP из gwp_constants.py
    GWP_VALUES = GWP_AR5_100Y

    # Коэффициенты аллометрических уравнений (Таблица 24)
    ALLOMETRIC_COEFFICIENTS = {
        "ель": {
            "надземная": {"a": 0.0533, "b": 0.8955},
            "корни": {"a": 0.0239, "b": 0.8408},
            "всего": {"a": 0.1237, "b": 0.8332},
        },
        "сосна": {
            "надземная": {"a": 0.0217, "b": 0.9817},
            "корни": {"a": 0.0387, "b": 0.7281},
            "всего": {"a": 0.0557, "b": 0.9031},
        },
        "береза": {
            "надземная": {"a": 0.5443, "b": 0.6527},
            "корни": {"a": 0.0387, "b": 0.7281},  # Используем как для сосны
            "всего": {"a": 0.0557, "b": 0.9031},
        },
    }

    # Коэффициенты выбросов при пожарах (Таблица 24.2)
    FIRE_EMISSION_FACTORS = {
        "CO2": 1569,  # г/кг сжигаемого вещества
        "CH4": 4.7,
        "N2O": 0.26,
    }

    def calculate_carbon_stock_change(
        self,
        biomass_change: float,
        deadwood_change: float,
        litter_change: float,
        soil_change: float,
    ) -> float:
        """
        Формула 1: Суммарное изменение запасов углерода.
        ΔC = ΔC_биомасса + ΔC_мертвая_древесина + ΔC_подстилка + ΔC_почва

        :param biomass_change: Изменение в биомассе, т C/год
        :param deadwood_change: Изменение в мертвой древесине, т C/год
        :param litter_change: Изменение в подстилке, т C/год
        :param soil_change: Изменение в почве, т C/год
        :return: Суммарное изменение, т C/год
        """
        return biomass_change + deadwood_change + litter_change + soil_change

    def calculate_biomass_change(
        self,
        carbon_after: float,
        carbon_before: float,
        area: float,
        period_years: float,
    ) -> float:
        """
        Формула 2: Изменение запасов углерода в биомассе.
        ΔC_биомасса = (C_после - C_до) × A_лесовосстановление / D

        :param carbon_after: Запас углерода после, т C/га
        :param carbon_before: Запас углерода до, т C/га
        :param area: Площадь лесовосстановления, га
        :param period_years: Продолжительность периода, лет
        :return: Изменение запасов, т C/год
        """
        if period_years <= 0:
            raise ValueError("Период должен быть больше 0")
        return (carbon_after - carbon_before) * area / period_years

    def calculate_tree_biomass(
        self, diameter: float, height: float, species: str, component: str = "всего"
    ) -> float:
        """
        Формула 3: Биомасса дерева через аллометрические уравнения.
        Биомасса = a × D^b или Биомасса = a × (D² × H)^b

        :param diameter: Диаметр ствола на высоте 1.3м, см
        :param height: Высота дерева, м
        :param species: Порода дерева
        :param component: Компонент биомассы ('надземная', 'корни', 'всего')
        :return: Биомасса, кг
        """
        if species not in self.ALLOMETRIC_COEFFICIENTS:
            raise ValueError(f"Неизвестная порода: {species}")

        coeffs = self.ALLOMETRIC_COEFFICIENTS[species].get(component)
        if not coeffs:
            raise ValueError(f"Неизвестный компонент: {component}")

        a, b = coeffs["a"], coeffs["b"]

        # Формула зависит от породы
        if species in ["ель", "сосна"]:
            # Биомасса = a × D^b
            return a * (diameter**b)
        else:
            # Биомасса = a × (D² × H)^b
            return a * ((diameter**2 * height) ** b)

    def calculate_carbon_from_biomass(self, biomass_kg: float) -> float:
        """
        Формула 4: Расчет углерода из биомассы.
        C = Биомасса × 0.5

        :param biomass_kg: Биомасса, кг
        :return: Углерод, т C
        """
        return biomass_kg * 0.5 / 1000

    def calculate_soil_carbon(
        self, organic_matter_percent: float, depth_cm: float, bulk_density: float
    ) -> float:
        """
        Формула 5: Запас углерода в почве.
        C_почва = Орг% × H × Об.масса × 58/100

        :param organic_matter_percent: Содержание органического вещества, %
        :param depth_cm: Глубина отбора проб, см
        :param bulk_density: Объемная масса почвы, г/см³
        :return: Запас углерода, т C/га
        """
        return organic_matter_percent * depth_cm * bulk_density * 0.58

    def calculate_fire_emissions(
        self,
        burned_area: float,
        available_fuel: float,
        combustion_factor: float,
        gas_type: str = "CO2",
    ) -> float:
        """
        Формула 6: Выбросы ПГ от пожаров.
        L_пожар = A × M_B × C_f × G_ef × 10^-3

        :param burned_area: Выжигаемая площадь, га
        :param available_fuel: Масса топлива, т/га
        :param combustion_factor: Коэффициент сгорания (0.43 для верхового, 0.15 для низового)
        :param gas_type: Тип газа (CO2, CH4, N2O)
        :return: Выбросы газа, т
        """
        emission_factor = self.FIRE_EMISSION_FACTORS.get(gas_type, 0)
        return (
            burned_area * available_fuel * combustion_factor * emission_factor * 0.001
        )

    def calculate_drained_soil_co2(self, area: float, ef: float = 0.71) -> float:
        """
        Формула 7: Выбросы CO2 от осушенных почв.
        CO2_organic = A × EF × CARBON_TO_CO2_FACTOR

        :param area: Площадь осушенных почв, га
        :param ef: Коэффициент выброса, т C/га/год (по умолчанию 0.71)
        :return: Выбросы CO2, т/год
        """
        return area * ef * CARBON_TO_CO2_FACTOR

    def calculate_drained_soil_n2o(self, area: float, ef: float = 1.71) -> float:
        """
        Формула 8: Выбросы N2O от осушенных почв.
        N2O_organic = A × EF × N2O_N_TO_N2O_FACTOR

        :param area: Площадь осушенных почв, га
        :param ef: Коэффициент выброса N2O, кг N/га/год
        :return: Выбросы N2O, т/год
        """
        return area * ef * N2O_N_TO_N2O_FACTOR / 1000

    def calculate_drained_soil_ch4(
        self,
        area: float,
        frac_ditch: float = 0.025,
        ef_land: float = 4.5,
        ef_ditch: float = 217,
    ) -> float:
        """
        Формула 9: Выбросы CH4 от осушенных почв.
        CH4_organic = A × (1-Frac_ditch) × EF_land + A × Frac_ditch × EF_ditch

        :param area: Площадь, га
        :param frac_ditch: Доля канав
        :param ef_land: Коэффициент для земель, кг CH4/га/год
        :param ef_ditch: Коэффициент для канав, кг CH4/га/год
        :return: Выбросы CH4, кг/год
        """
        return area * ((1 - frac_ditch) * ef_land + frac_ditch * ef_ditch)

    def calculate_fuel_emissions(
        self, fuel_volumes: Dict[str, float], emission_factors: Dict[str, float]
    ) -> float:
        """
        Формула 10: Эмиссия CO2 от сжигания топлива.
        C_FUEL = Σ(V_k × EF_k)

        :param fuel_volumes: Объемы топлива по видам
        :param emission_factors: Коэффициенты выбросов по видам
        :return: Выбросы углерода, т C
        """
        return sum(
            volume * emission_factors.get(fuel_type, 0)
            for fuel_type, volume in fuel_volumes.items()
        )

    def carbon_to_co2(self, carbon: float) -> float:
        """
        Формула 11: Перевод углерода в CO2.
        CO2 = ΔC × (-CARBON_TO_CO2_FACTOR)

        ВАЖНО: Отрицательный знак используется потому что:
        - Положительное ΔC = поглощение углерода = УДАЛЕНИЕ CO2 из атмосферы (отрицательные выбросы)
        - Отрицательное ΔC = потери углерода = выбросы CO2 в атмосферу

        :param carbon: Изменение запасов углерода, т C
        :return: CO2, т (отрицательное значение = поглощение)
        """
        return carbon * (-CARBON_TO_CO2_FACTOR)

    def to_co2_equivalent(self, gas_amount: float, gas_type: str) -> float:
        """
        Формула 12: Перевод в CO2-эквивалент.
        CO2-экв = ПГ × ПГП

        ИСПРАВЛЕНО: Использованы актуальные значения GWP согласно AR5 IPCC (2014)

        :param gas_amount: Количество газа, т
        :param gas_type: Тип газа (CH4, N2O, CO2)
        :return: CO2-эквивалент, т CO2-экв
        """
        if gas_type not in self.GWP_VALUES:
            raise ValueError(
                f"Неизвестный тип газа: {gas_type}. Доступные: {list(self.GWP_VALUES.keys())}"
            )

        return gas_amount * self.GWP_VALUES[gas_type]


class LandReclamationCalculator:
    """Калькулятор для рекультивации земель (формулы 13-26)."""

    # Используем централизованные значения GWP из gwp_constants.py
    GWP_VALUES = GWP_AR5_100Y

    def calculate_conversion_carbon_change(
        self, biomass_change: float, soil_change: float
    ) -> float:
        """
        Формула 13: Изменение запасов углерода при рекультивации.
        ΔC_конверсия = ΔC_биомасса + ΔC_почва
        """
        return biomass_change + soil_change

    def calculate_reclamation_biomass_change(
        self,
        carbon_after: float,
        carbon_before: float,
        area: float,
        period_years: float,
    ) -> float:
        """
        Формула 14: Изменение запасов углерода в биомассе рекультивированных земель.
        ΔC_биомасса = (C_после - C_до) × A_рекультивация / D
        """
        if period_years <= 0:
            raise ValueError("Период должен быть больше 0")
        return (carbon_after - carbon_before) * area / period_years

    def calculate_reclamation_soil_change(
        self, soil_after: float, soil_before: float, area: float, period_years: float
    ) -> float:
        """
        Формула 15: Изменение запасов углерода в почве рекультивированных земель.
        ΔC_почва = (C_после_почва - C_до_почва) × A_рекультивация / D
        """
        if period_years <= 0:
            raise ValueError("Период должен быть больше 0")
        return (soil_after - soil_before) * area / period_years

    def calculate_grassland_carbon(
        self, aboveground_carbon: float, belowground_carbon: float
    ) -> float:
        """
        Формула 20: Запас углерода в травянистой биомассе.
        C_биомасса = C_надз.биомасса + C_подз.биомасса
        """
        return aboveground_carbon + belowground_carbon

    def calculate_aboveground_grass_carbon(
        self, dry_weight: float, area_correction: float = 0.04
    ) -> float:
        """
        Формула 21: Углерод в надземной травянистой биомассе.
        C_надз.биомасса = Вес × 0.04 × 0.5

        :param dry_weight: Абсолютно сухой вес пробы, кг
        :param area_correction: Коэффициент площади (по умолчанию 0.04)
        :return: Углерод, т C/га
        """
        return dry_weight * area_correction * 0.5

    def calculate_belowground_grass_carbon(
        self, aboveground_carbon: float, a: float = 0.922, b: float = 1.057
    ) -> float:
        """
        Формула 22: Углерод в подземной травянистой биомассе.
        C_подз.биомасса = [a × (C_надз × 20) + b] × 0.45 / 10

        :param aboveground_carbon: Углерод надземной биомассы, т C/га
        :param a, b: Коэффициенты уравнения
        :return: Углерод подземной биомассы, т C/га
        """
        return (a * (aboveground_carbon * 20) + b) * 0.45 / 10

    def calculate_soil_carbon_from_organic(
        self, organic_percent: float, depth_cm: float, bulk_density: float
    ) -> float:
        """
        Формула 23: Запас углерода в почве.
        C_почва = Орг% × H × Об.масса × 58/100

        Аналогично формуле 5
        """
        return organic_percent * depth_cm * bulk_density * 0.58

    def calculate_fossil_fuel_emissions(
        self, fuel_data: List[Tuple[float, float]]
    ) -> float:
        """
        Формула 24: Эмиссия CO2 от сжигания ископаемого топлива.
        C_FUEL = Σ(V_k × EF_k)

        :param fuel_data: Список кортежей (объем, коэффициент_выброса)
        :return: Выбросы углерода, т C
        """
        return sum(volume * ef for volume, ef in fuel_data)

    def carbon_to_co2_conversion(self, carbon_change: float) -> float:
        """
        Формула 25: Перевод углерода в CO2.
        CO2 = ΔC × (-CARBON_TO_CO2_FACTOR)

        ВАЖНО: См. комментарий к формуле 11 в ForestRestorationCalculator
        """
        return carbon_change * (-CARBON_TO_CO2_FACTOR)

    def ghg_to_co2_equivalent(self, gas_amount: float, gas_type: str) -> float:
        """
        Формула 26: Пересчет в CO2-эквивалент.
        CO2-экв = ПГ × ПГП

        ИСПРАВЛЕНО: Использованы актуальные значения GWP согласно AR5 IPCC (2014)

        :param gas_amount: Количество газа, т
        :param gas_type: Тип газа ('CH4', 'N2O' или 'CO2')
        :return: CO2-эквивалент, т CO2-экв
        """
        if gas_type not in self.GWP_VALUES:
            raise ValueError(
                f"Неизвестный тип газа: {gas_type}. Доступные: {list(self.GWP_VALUES.keys())}"
            )

        return gas_amount * self.GWP_VALUES[gas_type]
