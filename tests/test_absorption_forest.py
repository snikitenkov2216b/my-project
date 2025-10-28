# tests/test_absorption_forest.py
"""
Тесты для модулей поглощения ПГ - лесовосстановление (формулы 1-26).
"""
import pytest
import math
from calculations.absorption_forest_restoration import (
    ForestRestorationCalculator,
    LandReclamationCalculator,
    ForestInventoryData,
)
from config import CARBON_TO_CO2_FACTOR, N2O_N_TO_N2O_FACTOR


class TestForestRestorationCalculator:
    """Тесты для ForestRestorationCalculator (формулы 1-12)."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.calc = ForestRestorationCalculator()

    def test_calculate_carbon_stock_change_formula_1(self):
        """Тест формулы 1: Суммарное изменение запасов углерода."""
        # ΔC = ΔC_биомасса + ΔC_мертвая_древесина + ΔC_подстилка + ΔC_почва
        biomass = 100.0
        deadwood = 20.0
        litter = 15.0
        soil = 50.0

        result = self.calc.calculate_carbon_stock_change(
            biomass, deadwood, litter, soil
        )

        expected = 100.0 + 20.0 + 15.0 + 50.0
        assert result == expected
        assert result == 185.0

    def test_calculate_biomass_change_formula_2(self):
        """Тест формулы 2: Изменение запасов углерода в биомассе."""
        # ΔC_биомасса = (C_после - C_до) × A_лесовосстановление / D
        carbon_after = 150.0  # т C/га
        carbon_before = 50.0  # т C/га
        area = 100.0  # га
        period_years = 20.0  # лет

        result = self.calc.calculate_biomass_change(
            carbon_after, carbon_before, area, period_years
        )

        expected = (150.0 - 50.0) * 100.0 / 20.0
        assert result == expected
        assert result == 500.0

    def test_calculate_biomass_change_zero_period_raises_error(self):
        """Проверка ошибки при нулевом периоде."""
        with pytest.raises(ValueError, match="Период должен быть больше 0"):
            self.calc.calculate_biomass_change(150.0, 50.0, 100.0, 0.0)

    def test_calculate_tree_biomass_formula_3_conifer(self):
        """Тест формулы 3: Биомасса дерева (хвойные породы)."""
        # Для ели: Биомасса = a × D^b
        diameter = 30.0  # см
        height = 25.0  # м
        species = "ель"

        result = self.calc.calculate_tree_biomass(diameter, height, species, "всего")

        # Коэффициенты для ели "всего": a=0.1237, b=0.8332
        expected = 0.1237 * (30.0**0.8332)
        assert abs(result - expected) < 0.01

    def test_calculate_tree_biomass_formula_3_deciduous(self):
        """Тест формулы 3: Биомасса дерева (лиственные породы)."""
        # Для березы: Биомасса = a × (D² × H)^b
        diameter = 25.0  # см
        height = 20.0  # м
        species = "береза"

        result = self.calc.calculate_tree_biomass(diameter, height, species, "всего")

        # Коэффициенты для березы "всего": a=0.0557, b=0.9031
        expected = 0.0557 * ((25.0**2 * 20.0) ** 0.9031)
        assert abs(result - expected) < 0.01

    def test_calculate_tree_biomass_unknown_species_raises_error(self):
        """Проверка ошибки при неизвестной породе."""
        with pytest.raises(ValueError, match="Неизвестная порода"):
            self.calc.calculate_tree_biomass(30.0, 25.0, "неизвестная", "всего")

    def test_calculate_carbon_from_biomass_formula_4(self):
        """Тест формулы 4: Расчет углерода из биомассы."""
        # C = Биомасса × 0.5 / 1000
        biomass_kg = 5000.0  # кг

        result = self.calc.calculate_carbon_from_biomass(biomass_kg)

        expected = 5000.0 * 0.5 / 1000
        assert result == expected
        assert result == 2.5  # т C

    def test_calculate_soil_carbon_formula_5(self):
        """Тест формулы 5: Запас углерода в почве."""
        # C_почва = Орг% × H × Об.масса × 0.58
        organic_percent = 3.5  # %
        depth_cm = 30.0  # см
        bulk_density = 1.2  # г/см³

        result = self.calc.calculate_soil_carbon(
            organic_percent, depth_cm, bulk_density
        )

        expected = 3.5 * 30.0 * 1.2 * 0.58
        assert result == expected
        assert abs(result - 73.08) < 0.01

    def test_calculate_fire_emissions_formula_6_co2(self):
        """Тест формулы 6: Выбросы CO2 от пожаров."""
        # L_пожар = A × M_B × C_f × G_ef × 10^-3
        burned_area = 100.0  # га
        available_fuel = 50.0  # т/га
        combustion_factor = 0.43  # верховой пожар
        gas_type = "CO2"

        result = self.calc.calculate_fire_emissions(
            burned_area, available_fuel, combustion_factor, gas_type
        )

        # Коэффициент для CO2 = 1569 г/кг
        expected = 100.0 * 50.0 * 0.43 * 1569 * 0.001
        assert result == expected
        assert abs(result - 3373.35) < 0.01

    def test_calculate_fire_emissions_formula_6_ch4(self):
        """Тест формулы 6: Выбросы CH4 от пожаров."""
        burned_area = 100.0  # га
        available_fuel = 50.0  # т/га
        combustion_factor = 0.15  # низовой пожар
        gas_type = "CH4"

        result = self.calc.calculate_fire_emissions(
            burned_area, available_fuel, combustion_factor, gas_type
        )

        # Коэффициент для CH4 = 4.7 г/кг
        expected = 100.0 * 50.0 * 0.15 * 4.7 * 0.001
        assert result == expected
        assert abs(result - 3.525) < 0.01

    def test_calculate_drained_soil_co2_formula_7(self):
        """Тест формулы 7: Выбросы CO2 от осушенных почв."""
        # CO2_organic = A × EF × CARBON_TO_CO2_FACTOR
        area = 100.0  # га
        ef = 0.71  # т C/га/год

        result = self.calc.calculate_drained_soil_co2(area, ef)

        expected = 100.0 * 0.71 * CARBON_TO_CO2_FACTOR
        assert abs(result - expected) < 0.1

    def test_calculate_drained_soil_n2o_formula_8(self):
        """Тест формулы 8: Выбросы N2O от осушенных почв."""
        # N2O_organic = A × EF × N2O_N_TO_N2O_FACTOR / 1000
        area = 100.0  # га
        ef = 1.71  # кг N/га/год

        result = self.calc.calculate_drained_soil_n2o(area, ef)

        expected = 100.0 * 1.71 * N2O_N_TO_N2O_FACTOR / 1000
        assert abs(result - expected) < 0.01
        assert abs(result - 0.268719) < 0.001

    def test_calculate_drained_soil_ch4_formula_9(self):
        """Тест формулы 9: Выбросы CH4 от осушенных почв."""
        # CH4_organic = A × (1-Frac_ditch) × EF_land + A × Frac_ditch × EF_ditch
        area = 100.0  # га
        frac_ditch = 0.025  # доля канав
        ef_land = 4.5  # кг CH4/га/год
        ef_ditch = 217.0  # кг CH4/га/год

        result = self.calc.calculate_drained_soil_ch4(
            area, frac_ditch, ef_land, ef_ditch
        )

        expected = 100.0 * ((1 - 0.025) * 4.5 + 0.025 * 217.0)
        assert abs(result - expected) < 0.2

    def test_calculate_fuel_emissions_formula_10(self):
        """Тест формулы 10: Эмиссия CO2 от сжигания топлива."""
        # C_FUEL = Σ(V_k × EF_k)
        fuel_volumes = {"дизель": 1000.0, "бензин": 500.0}
        emission_factors = {"дизель": 0.02, "бензин": 0.018}

        result = self.calc.calculate_fuel_emissions(fuel_volumes, emission_factors)

        expected = 1000.0 * 0.02 + 500.0 * 0.018
        assert result == expected
        assert result == 29.0

    def test_carbon_to_co2_formula_11_absorption(self):
        """Тест формулы 11: Перевод углерода в CO2 (поглощение)."""
        # CO2 = ΔC × (-CARBON_TO_CO2_FACTOR)
        # Положительное ΔC = поглощение = отрицательные выбросы
        carbon_absorbed = 100.0  # т C (поглощено)

        result = self.calc.carbon_to_co2(carbon_absorbed)

        expected = 100.0 * (-CARBON_TO_CO2_FACTOR)
        assert abs(result - expected) < 0.1
        assert result < 0  # Отрицательное = поглощение

    def test_carbon_to_co2_formula_11_emission(self):
        """Тест формулы 11: Перевод углерода в CO2 (выбросы)."""
        # Отрицательное ΔC = потери углерода = выбросы CO2
        carbon_lost = -50.0  # т C (потеряно)

        result = self.calc.carbon_to_co2(carbon_lost)

        expected = -50.0 * (-CARBON_TO_CO2_FACTOR)
        assert abs(result - expected) < 0.1
        assert result > 0  # Положительное = выбросы

    def test_to_co2_equivalent_formula_12_ch4(self):
        """Тест формулы 12: Перевод CH4 в CO2-эквивалент."""
        # CO2-экв = ПГ × ПГП
        ch4_amount = 10.0  # т CH4
        gas_type = "CH4"

        result = self.calc.to_co2_equivalent(ch4_amount, gas_type)

        # GWP для CH4 = 28 (AR5 IPCC 2014)
        expected = 10.0 * 28
        assert result == expected
        assert result == 280.0

    def test_to_co2_equivalent_formula_12_n2o(self):
        """Тест формулы 12: Перевод N2O в CO2-эквивалент."""
        n2o_amount = 5.0  # т N2O
        gas_type = "N2O"

        result = self.calc.to_co2_equivalent(n2o_amount, gas_type)

        # GWP для N2O = 265 (AR5 IPCC 2014)
        expected = 5.0 * 265
        assert result == expected
        assert result == 1325.0

    def test_to_co2_equivalent_unknown_gas_raises_error(self):
        """Проверка ошибки при неизвестном газе."""
        with pytest.raises(ValueError):
            self.calc.to_co2_equivalent(10.0, "UNKNOWN_GAS")


class TestLandReclamationCalculator:
    """Тесты для LandReclamationCalculator (формулы 13-26)."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.calc = LandReclamationCalculator()

    def test_calculate_conversion_carbon_change_formula_13(self):
        """Тест формулы 13: Изменение запасов углерода при рекультивации."""
        # ΔC_конверсия = ΔC_биомасса + ΔC_почва
        biomass_change = 80.0  # т C/год
        soil_change = 120.0  # т C/год

        result = self.calc.calculate_conversion_carbon_change(
            biomass_change, soil_change
        )

        expected = 80.0 + 120.0
        assert result == expected
        assert result == 200.0

    def test_calculate_reclamation_biomass_change_formula_14(self):
        """Тест формулы 14: Изменение запасов углерода в биомассе."""
        # ΔC_биомасса = (C_после - C_до) × A_рекультивация / D
        carbon_after = 200.0
        carbon_before = 20.0
        area = 50.0
        period_years = 15.0

        result = self.calc.calculate_reclamation_biomass_change(
            carbon_after, carbon_before, area, period_years
        )

        expected = (200.0 - 20.0) * 50.0 / 15.0
        assert result == expected
        assert result == 600.0

    def test_calculate_grassland_carbon_formula_20(self):
        """Тест формулы 20: Запас углерода в травянистой биомассе."""
        # C_биомасса = C_надз.биомасса + C_подз.биомасса
        aboveground = 5.0
        belowground = 15.0

        result = self.calc.calculate_grassland_carbon(aboveground, belowground)

        assert result == 20.0

    def test_calculate_aboveground_grass_carbon_formula_21(self):
        """Тест формулы 21: Углерод в надземной травянистой биомассе."""
        # C_надз.биомасса = Вес × 0.04 × 0.5
        dry_weight = 1000.0  # кг
        area_correction = 0.04

        result = self.calc.calculate_aboveground_grass_carbon(
            dry_weight, area_correction
        )

        expected = 1000.0 * 0.04 * 0.5
        assert result == expected
        assert result == 20.0

    def test_calculate_belowground_grass_carbon_formula_22(self):
        """Тест формулы 22: Углерод в подземной травянистой биомассе."""
        # C_подз.биомасса = [a × (C_надз × 20) + b] × 0.45 / 10
        aboveground_carbon = 5.0  # т C/га
        a = 0.922
        b = 1.057

        result = self.calc.calculate_belowground_grass_carbon(aboveground_carbon, a, b)

        expected = (a * (5.0 * 20) + b) * 0.45 / 10
        assert abs(result - expected) < 0.01
        assert abs(result - 4.19967) < 0.01

    def test_carbon_to_co2_conversion_formula_25(self):
        """Тест формулы 25: Перевод углерода в CO2."""
        # CO2 = ΔC × (-CARBON_TO_CO2_FACTOR)
        carbon_change = 150.0

        result = self.calc.carbon_to_co2_conversion(carbon_change)

        expected = 150.0 * (-CARBON_TO_CO2_FACTOR)
        assert abs(result - expected) < 0.01
        assert result < 0  # Поглощение

    def test_ghg_to_co2_equivalent_formula_26(self):
        """Тест формулы 26: Пересчет в CO2-эквивалент."""
        # CO2-экв = ПГ × ПГП
        ch4_amount = 20.0
        gas_type = "CH4"

        result = self.calc.ghg_to_co2_equivalent(ch4_amount, gas_type)

        expected = 20.0 * 28
        assert result == expected
        assert result == 560.0
