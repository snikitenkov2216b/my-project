# tests/test_absorption_agricultural.py
"""
Тесты для модулей поглощения ПГ - сельскохозяйственные угодья (формулы 75-100).
"""
import pytest
from calculations.absorption_agricultural import (
    AgriculturalLandCalculator,
    LandConversionCalculator,
    CropData,
    LivestockData,
)
from config import CARBON_TO_CO2_FACTOR


class TestAgriculturalLandCalculator:
    """Тесты для AgriculturalLandCalculator (формулы 75-90)."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.calc = AgriculturalLandCalculator()

    def test_calculate_drained_ch4_emissions_formula_75(self):
        """Тест формулы 75: Выбросы CH4 от осушенных органогенных почв."""
        # CH4_organic = A × (1 - Frac_ditch) × EF_land + A × Frac_ditch × EF_ditch
        area = 100.0  # га
        frac_ditch = 0.05
        ef_land = 1.4  # кг CH4/га/год
        ef_ditch = 43.63  # кг CH4/га/год

        result = self.calc.calculate_drained_ch4_emissions(
            area, frac_ditch, ef_land, ef_ditch
        )

        expected = 100.0 * ((1 - 0.05) * 1.4 + 0.05 * 43.63)
        assert abs(result - expected) < 0.5

    def test_calculate_fire_emissions_formula_76(self):
        """Тест формулы 76: Выбросы ПГ от пожаров."""
        # L_пожар = A × MB × C_f × G_ef × 10^-3
        area = 50.0  # га
        biomass_mass = 30.0  # т/га
        combustion_factor = 0.9  # доля
        emission_factor = 1569.0  # г/кг (CO2)

        result = self.calc.calculate_fire_emissions(
            area, biomass_mass, combustion_factor, emission_factor
        )

        expected = 50.0 * 30.0 * 0.9 * 1569.0 * 0.001
        assert abs(result - expected) < 0.01
        assert abs(result - 2118.15) < 0.01

    def test_calculate_biomass_carbon_change_formula_77(self):
        """Тест формулы 77: Изменение запасов углерода в биомассе."""
        # ΔC = ΔC_G - ΔC_L
        carbon_gain = 500.0  # т C/год
        carbon_loss = 150.0  # т C/год

        result = self.calc.calculate_biomass_carbon_change(carbon_gain, carbon_loss)

        expected = 500.0 - 150.0
        assert result == expected
        assert result == 350.0

    def test_calculate_carbon_gain_formula_78(self):
        """Тест формулы 78: Прирост углерода."""
        # ΔC_G = C_gain × A_gain
        carbon_per_ha = 5.0  # т C/га/год
        area_gain = 100.0  # га

        result = self.calc.calculate_carbon_gain(carbon_per_ha, area_gain)

        expected = 5.0 * 100.0
        assert result == expected
        assert result == 500.0

    def test_calculate_carbon_loss_formula_79(self):
        """Тест формулы 79: Потери углерода."""
        # ΔC_L = C_loss × A_loss
        carbon_per_ha = 3.0  # т C/га/год
        area_loss = 50.0  # га

        result = self.calc.calculate_carbon_loss(carbon_per_ha, area_loss)

        expected = 3.0 * 50.0
        assert result == expected
        assert result == 150.0

    def test_calculate_mineral_soil_carbon_change_formula_80(self):
        """Тест формулы 80: Изменение запасов углерода в минеральных почвах."""
        # ΔC_минеральные = (Cfert + Clime + Cplant) - (Cresp + Cerosion)
        c_fertilizer = 200.0
        c_lime = 50.0
        c_plant = 300.0
        c_respiration = 150.0
        c_erosion = 80.0

        result = self.calc.calculate_mineral_soil_carbon_change(
            c_fertilizer, c_lime, c_plant, c_respiration, c_erosion
        )

        inputs = 200.0 + 50.0 + 300.0
        outputs = 150.0 + 80.0
        expected = inputs - outputs
        assert result == expected
        assert result == 320.0

    def test_calculate_fertilizer_carbon_formula_81(self):
        """Тест формулы 81: Углерод от удобрений."""
        # Cfert = Σ(Орг_i × C_орг_i) + Σ(Мин_j × C_мин_j)
        organic_fertilizers = {
            "навоз": (100.0, 0.4),  # (количество, содержание C)
            "компост": (50.0, 0.3),
        }
        mineral_fertilizers = {
            "мочевина": (30.0, 0.2),  # (количество, коэффициент C)
        }

        result = self.calc.calculate_fertilizer_carbon(
            organic_fertilizers, mineral_fertilizers
        )

        organic_c = 100.0 * 0.4 + 50.0 * 0.3
        mineral_c = 30.0 * 0.2
        expected = organic_c + mineral_c
        assert result == expected
        assert result == 61.0

    def test_calculate_lime_carbon_formula_82(self):
        """Тест формулы 82: Углерод от извести."""
        # Clime = Lime × 8.75/100
        lime_amount = 1000.0  # т/год

        result = self.calc.calculate_lime_carbon(lime_amount)

        expected = 1000.0 * 0.0875
        assert result == expected
        assert result == 87.5

    def test_calculate_plant_residue_carbon_formula_83(self):
        """Тест формулы 83: Углерод от растительных остатков."""
        # Cplant = C_ab + C_un
        aboveground_carbon = 200.0  # т C/год
        underground_carbon = 300.0  # т C/год

        result = self.calc.calculate_plant_residue_carbon(
            aboveground_carbon, underground_carbon
        )

        expected = 200.0 + 300.0
        assert result == expected
        assert result == 500.0

    def test_calculate_crop_residue_carbon_formula_84(self):
        """Тест формулы 84: Углерод от остатков культур."""
        # C_ab или C_un = Σ((a_i × Y_i + b_i) × C_i) × S_i
        crops = [
            CropData("пшеница", yield_value=35.0, area=100.0, carbon_content=0.45),
            CropData("кукуруза", yield_value=50.0, area=50.0, carbon_content=0.48),
        ]
        a_coef = {"пшеница": 0.3, "кукуруза": 0.35}
        b_coef = {"пшеница": 3.0, "кукуруза": 4.0}

        result = self.calc.calculate_crop_residue_carbon(crops, a_coef, b_coef)

        # Пшеница: (0.3 × 35 + 3.0) × 0.45 × 100
        crop1 = (0.3 * 35.0 + 3.0) * 0.45 * 100.0
        # Кукуруза: (0.35 × 50 + 4.0) × 0.48 × 50
        crop2 = (0.35 * 50.0 + 4.0) * 0.48 * 50.0
        expected = crop1 + crop2
        assert abs(result - expected) < 0.01

    def test_calculate_erosion_losses_formula_85(self):
        """Тест формулы 85: Потери углерода от эрозии."""
        # Cerosion = A × EFerosion
        area = 500.0  # га
        erosion_factor = 0.5  # т C/га/год

        result = self.calc.calculate_erosion_losses(area, erosion_factor)

        expected = 500.0 * 0.5
        assert result == expected
        assert result == 250.0

    def test_calculate_soil_respiration_formula_86(self):
        """Тест формулы 86: Потери углерода от дыхания почвы."""
        # Cresp = Σ((Area_i × AC_CO2i × Veg × 0.6 × 1.43) / 100) × 12/44
        area = 100.0  # га
        co2_emission_rate = 250.0  # мг CO2/м²/час
        vegetation_period = 150.0  # дни
        conversion_factor = 0.6

        result = self.calc.calculate_soil_respiration(
            area, co2_emission_rate, vegetation_period, conversion_factor
        )

        co2_emission = (
            100.0 * 250.0 * 150.0 * 0.6 * 1.43
        ) / 100
        expected = co2_emission * (12 / 44)
        assert abs(result - expected) < 0.01

    def test_calculate_organic_soil_co2_formula_87(self):
        """Тест формулы 87: Выбросы CO2 от органогенных почв."""
        # CO2_organic = A × EF_C_CO2 × CARBON_TO_CO2_FACTOR
        area = 100.0  # га
        ef = 5.9  # т C/га/год

        result = self.calc.calculate_organic_soil_co2(area, ef)

        expected = 100.0 * 5.9 * CARBON_TO_CO2_FACTOR
        assert abs(result - expected) < 2.0

    def test_calculate_organic_soil_n2o_formula_88(self):
        """Тест формулы 88: Выбросы N2O от органогенных почв."""
        # N2O_organic = A × EF_N_N2O × 44/28 / 1000
        area = 100.0  # га
        ef = 7.0  # кг N/га/год

        result = self.calc.calculate_organic_soil_n2o(area, ef)

        expected = 100.0 * 7.0 * (44 / 28) / 1000
        assert abs(result - expected) < 0.001
        assert abs(result - 1.1) < 0.01

    def test_calculate_organic_soil_ch4_formula_89(self):
        """Тест формулы 89: Выбросы CH4 от органогенных почв."""
        # CH4_organic = A × (1 - Frac_ditch) × EF_land + A × Frac_ditch × EF_ditch
        area = 100.0  # га
        frac_ditch = 0.5
        ef_land = 0.0  # кг CH4/га/год
        ef_ditch = 1165.0  # кг CH4/га/год

        result = self.calc.calculate_organic_soil_ch4(
            area, frac_ditch, ef_land, ef_ditch
        )

        expected = 100.0 * ((1 - 0.5) * 0.0 + 0.5 * 1165.0)
        assert abs(result - expected) < 0.01
        assert abs(result - 58250.0) < 0.1

    def test_calculate_agricultural_fire_emissions_formula_90(self):
        """Тест формулы 90: Выбросы от пожаров на сельхозземлях."""
        # L_пожар = A × MB × C_f × G_ef × 10^-3
        area = 80.0  # га
        biomass = 20.0  # т/га
        combustion = 0.85  # доля
        emission_factor = 1569.0  # г/кг (CO2)

        result = self.calc.calculate_agricultural_fire_emissions(
            area, biomass, combustion, emission_factor
        )

        expected = 80.0 * 20.0 * 0.85 * 1569.0 * 0.001
        assert abs(result - expected) < 1.0


class TestLandConversionCalculator:
    """Тесты для LandConversionCalculator (формулы 91-100)."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.calc = LandConversionCalculator()

    def test_calculate_conversion_carbon_change_formula_91(self):
        """Тест формулы 91: Изменение запасов углерода при конверсии."""
        # ΔC_конверсия = (Σ C_после_i - C_до_i) × ΔA_в_пахотные / D
        carbon_after = [100.0, 50.0, 30.0]  # биомасса, подстилка, почва
        carbon_before = [150.0, 60.0, 40.0]
        conversion_area = 200.0  # га
        period = 20.0  # лет

        result = self.calc.calculate_conversion_carbon_change(
            carbon_after, carbon_before, conversion_area, period
        )

        total_change = sum(carbon_after) - sum(carbon_before)
        expected = total_change * conversion_area / period
        assert abs(result - expected) < 1.0  # потери углерода

    def test_calculate_conversion_carbon_change_zero_period_raises_error(self):
        """Проверка ошибки при нулевом периоде."""
        with pytest.raises(ValueError, match="Период должен быть больше 0"):
            self.calc.calculate_conversion_carbon_change(
                [100.0], [150.0], 200.0, 0.0
            )

    def test_calculate_converted_land_co2_formula_92(self):
        """Тест формулы 92: Выбросы CO2 от осушенных почв переведенных земель."""
        # CO2_organic = A × EF_C_CO2 × CARBON_TO_CO2_FACTOR
        area = 100.0  # га
        ef = 5.9  # т C/га/год

        result = self.calc.calculate_converted_land_co2(area, ef)

        expected = 100.0 * 5.9 * CARBON_TO_CO2_FACTOR
        assert abs(result - expected) < 2.0

    def test_calculate_converted_land_n2o_formula_93(self):
        """Тест формулы 93: Выбросы N2O от осушенных почв переведенных земель."""
        # N2O_organic = A × EF_N_N2O × 44/28 / 1000
        area = 100.0  # га
        ef = 7.0  # кг N/га/год

        result = self.calc.calculate_converted_land_n2o(area, ef)

        expected = 100.0 * 7.0 * (44 / 28) / 1000
        assert abs(result - expected) < 0.001
        assert abs(result - 1.1) < 0.01

    def test_calculate_converted_land_ch4_formula_94(self):
        """Тест формулы 94: Выбросы CH4 от осушенных почв переведенных земель."""
        # CH4_organic = A × (1 - Frac_ditch) × EF_land + A × Frac_ditch × EF_ditch
        area = 100.0  # га
        frac_ditch = 0.5
        ef_land = 0.0
        ef_ditch = 1165.0

        result = self.calc.calculate_converted_land_ch4(
            area, frac_ditch, ef_land, ef_ditch
        )

        expected = 100.0 * ((1 - 0.5) * 0.0 + 0.5 * 1165.0)
        assert abs(result - expected) < 0.01
        assert abs(result - 58250.0) < 0.1

    def test_calculate_conversion_fire_emissions_formula_95(self):
        """Тест формулы 95: Выбросы от пожаров при конверсии земель."""
        # L_пожар = A × MB × C_f × G_ef × 10^-3
        area = 60.0  # га
        biomass = 40.0  # т/га
        combustion = 0.9  # доля
        emission_factor = 1569.0  # г/кг

        result = self.calc.calculate_conversion_fire_emissions(
            area, biomass, combustion, emission_factor
        )

        expected = 60.0 * 40.0 * 0.9 * 1569.0 * 0.001
        assert abs(result - expected) < 1.0

    def test_to_co2_equivalent_ch4(self):
        """Тест перевода CH4 в CO2-эквивалент."""
        ch4_amount = 15.0  # т CH4
        gas_type = "CH4"

        result = self.calc.to_co2_equivalent(ch4_amount, gas_type)

        # GWP для CH4 = 28 (AR5 IPCC 2014)
        expected = 15.0 * 28
        assert result == expected
        assert result == 420.0

    def test_to_co2_equivalent_n2o(self):
        """Тест перевода N2O в CO2-эквивалент."""
        n2o_amount = 3.0  # т N2O
        gas_type = "N2O"

        result = self.calc.to_co2_equivalent(n2o_amount, gas_type)

        # GWP для N2O = 265 (AR5 IPCC 2014)
        expected = 3.0 * 265
        assert result == expected
        assert result == 795.0

    def test_to_co2_equivalent_co2(self):
        """Тест перевода CO2 в CO2-эквивалент (должно быть 1:1)."""
        co2_amount = 1000.0  # т CO2
        gas_type = "CO2"

        result = self.calc.to_co2_equivalent(co2_amount, gas_type)

        # GWP для CO2 = 1
        expected = 1000.0 * 1
        assert result == expected
        assert result == 1000.0

    def test_to_co2_equivalent_unknown_gas_raises_error(self):
        """Проверка ошибки при неизвестном газе."""
        with pytest.raises(ValueError, match="Неизвестный тип газа"):
            self.calc.to_co2_equivalent(10.0, "HFC-134a")
