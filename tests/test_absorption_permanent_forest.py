# tests/test_absorption_permanent_forest.py
"""
Тесты для модулей поглощения ПГ - постоянные лесные земли (формулы 27-74).
"""
import pytest
from calculations.absorption_permanent_forest import (
    PermanentForestCalculator,
    ProtectiveForestCalculator,
    ForestStandData,
)
from config import CARBON_TO_CO2_FACTOR


class TestPermanentForestCalculator:
    """Тесты для PermanentForestCalculator (формулы 27-59)."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.calc = PermanentForestCalculator()

    def test_calculate_biomass_carbon_stock_formula_27(self):
        """Тест формулы 27: Запас углерода в биомассе древостоев."""
        # CP_ij = V_ij × KP_ij
        volume = 200.0  # м³
        conversion_factor = 0.25  # KP_ij

        result = self.calc.calculate_biomass_carbon_stock(volume, conversion_factor)

        expected = 200.0 * 0.25
        assert result == expected
        assert result == 50.0

    def test_calculate_mean_carbon_per_hectare_formula_28(self):
        """Тест формулы 28: Средний запас углерода на гектар."""
        # MCP_ij = CP_ij / S_ij
        carbon_stock = 1000.0  # т C
        area = 50.0  # га

        result = self.calc.calculate_mean_carbon_per_hectare(carbon_stock, area)

        expected = 1000.0 / 50.0
        assert result == expected
        assert result == 20.0

    def test_calculate_mean_carbon_per_hectare_zero_area_raises_error(self):
        """Проверка ошибки при нулевой площади."""
        with pytest.raises(ValueError, match="Площадь должна быть больше 0"):
            self.calc.calculate_mean_carbon_per_hectare(1000.0, 0.0)

    def test_calculate_carbon_absorption_rate_formula_29(self):
        """Тест формулы 29: Скорость абсорбции углерода."""
        # MAbP_ij = (MCP_ij - MCP_i-1,j)/(TI_i-1,j + TI_ij) +
        #           (MCP_i+1,j - MCP_ij)/(TI_ij + TI_i+1,j)
        mcp_current = 30.0  # т C/га
        mcp_prev = 20.0  # т C/га
        mcp_next = 40.0  # т C/га
        ti_prev = 10.0  # лет
        ti_current = 10.0  # лет
        ti_next = 10.0  # лет

        result = self.calc.calculate_carbon_absorption_rate(
            mcp_current, mcp_prev, mcp_next, ti_prev, ti_current, ti_next
        )

        term1 = (30.0 - 20.0) / (10.0 + 10.0)
        term2 = (40.0 - 30.0) / (10.0 + 10.0)
        expected = term1 + term2
        assert result == expected
        assert result == 1.0  # т C/га/год

    def test_calculate_total_absorption_formula_30(self):
        """Тест формулы 30: Общая абсорбция углерода."""
        # AbP_ij = S_ij × MAbP_ij
        area = 100.0  # га
        absorption_rate = 1.5  # т C/га/год

        result = self.calc.calculate_total_absorption(area, absorption_rate)

        expected = 100.0 * 1.5
        assert result == expected
        assert result == 150.0

    def test_calculate_annual_disturbance_rate_fire_formula_31(self):
        """Тест формулы 31: Годичный темп пожарных нарушений."""
        # ASF = SB / TRB
        burned_area = 500.0  # га
        rotation_period = 50.0  # лет

        result = self.calc.calculate_annual_disturbance_rate_fire(
            burned_area, rotation_period
        )

        expected = 500.0 / 50.0
        assert result == expected
        assert result == 10.0  # га/год

    def test_calculate_annual_disturbance_rate_fire_zero_period_raises_error(self):
        """Проверка ошибки при нулевом периоде ротации."""
        with pytest.raises(ValueError, match="Период ротации должен быть больше 0"):
            self.calc.calculate_annual_disturbance_rate_fire(500.0, 0.0)

    def test_calculate_annual_disturbance_rate_harvest_formula_32(self):
        """Тест формулы 32: Годичный темп рубок."""
        # ASH = SC / TRC
        harvested_area = 1000.0  # га
        rotation_period = 100.0  # лет

        result = self.calc.calculate_annual_disturbance_rate_harvest(
            harvested_area, rotation_period
        )

        expected = 1000.0 / 100.0
        assert result == expected
        assert result == 10.0  # га/год

    def test_calculate_harvest_biomass_loss_formula_33(self):
        """Тест формулы 33: Потери биомассы при сплошных рубках."""
        # LsPH = ASH × CP_m / S_m
        annual_harvest_area = 10.0  # га/год
        mean_carbon_stock = 5000.0  # т C
        mean_area = 100.0  # га

        result = self.calc.calculate_harvest_biomass_loss(
            annual_harvest_area, mean_carbon_stock, mean_area
        )

        expected = 10.0 * 5000.0 / 100.0
        assert result == expected
        assert result == 500.0  # т C/год

    def test_calculate_fire_biomass_loss_formula_34(self):
        """Тест формулы 34: Потери биомассы при пожарах."""
        # LsPF = ASF × CP_a / S_a
        annual_fire_area = 5.0  # га/год
        mean_carbon_stock = 3000.0  # т C
        mean_area = 50.0  # га

        result = self.calc.calculate_fire_biomass_loss(
            annual_fire_area, mean_carbon_stock, mean_area
        )

        expected = 5.0 * 3000.0 / 50.0
        assert result == expected
        assert result == 300.0  # т C/год

    def test_calculate_biomass_budget_formula_35(self):
        """Тест формулы 35: Годичный бюджет углерода биомассы."""
        # BP = AbP - LsPH - LsPF
        absorption = 1000.0  # т C/год
        harvest_loss = 400.0  # т C/год
        fire_loss = 100.0  # т C/год

        result = self.calc.calculate_biomass_budget(absorption, harvest_loss, fire_loss)

        expected = 1000.0 - 400.0 - 100.0
        assert result == expected
        assert result == 500.0  # т C/год (чистое поглощение)

    def test_calculate_deadwood_carbon_stock_formula_36(self):
        """Тест формулы 36: Запас углерода в мертвой древесине."""
        # CD_ij = V_ij × KD_ij
        volume = 50.0  # м³
        conversion_factor = 0.15  # KD_ij

        result = self.calc.calculate_deadwood_carbon_stock(volume, conversion_factor)

        expected = 50.0 * 0.15
        assert result == expected
        assert result == 7.5

    def test_calculate_litter_carbon_stock_formula_43(self):
        """Тест формулы 43: Запас углерода в подстилке."""
        # CL_ij = S_ij × KL_ij
        area = 100.0  # га
        litter_factor = 2.5  # т C/га

        result = self.calc.calculate_litter_carbon_stock(area, litter_factor)

        expected = 100.0 * 2.5
        assert result == expected
        assert result == 250.0

    def test_calculate_soil_carbon_stock_formula_49(self):
        """Тест формулы 49: Запас углерода в почве."""
        # CS_ij = S_ij × KS_ij
        area = 100.0  # га
        soil_factor = 80.0  # т C/га

        result = self.calc.calculate_soil_carbon_stock(area, soil_factor)

        expected = 100.0 * 80.0
        assert result == expected
        assert result == 8000.0

    def test_calculate_soil_absorption_formula_50(self):
        """Тест формулы 50: Абсорбция углерода почвой."""
        # MAbS_ij = (MCS_ij - MCS_i-1,j)/(TI_i-1,j - TI_ij) +
        #           (MCS_i+1,j - MCS_ij)/(TI_ij - TI_i+1,j)
        mcs_current = 80.0
        mcs_prev = 75.0
        mcs_next = 85.0
        ti_prev = 20.0
        ti_current = 10.0
        ti_next = 5.0  # изменено с 10.0 на 5.0 чтобы избежать деления на 0

        result = self.calc.calculate_soil_absorption(
            mcs_current, mcs_prev, mcs_next, ti_prev, ti_current, ti_next
        )

        term1 = (80.0 - 75.0) / (20.0 - 10.0)
        term2 = (85.0 - 80.0) / (10.0 - 5.0)
        expected = term1 + term2
        assert abs(result - expected) < 0.01
        assert result == 1.5  # т C/га/год

    def test_calculate_soil_budget_formula_54(self):
        """Тест формулы 54: Годичный бюджет углерода почвы."""
        # BS = AbS - LsSH - LsSF
        absorption = 200.0
        harvest_loss = 50.0
        fire_loss = 30.0

        result = self.calc.calculate_soil_budget(absorption, harvest_loss, fire_loss)

        expected = 200.0 - 50.0 - 30.0
        assert result == expected
        assert result == 120.0

    def test_calculate_total_budget_formula_55(self):
        """Тест формулы 55: Суммарный бюджет углерода."""
        # BT = BP + BD + BL + BS
        biomass_budget = 500.0
        deadwood_budget = 50.0
        litter_budget = 30.0
        soil_budget = 120.0

        result = self.calc.calculate_total_budget(
            biomass_budget, deadwood_budget, litter_budget, soil_budget
        )

        expected = 500.0 + 50.0 + 30.0 + 120.0
        assert result == expected
        assert result == 700.0

    def test_calculate_drained_forest_co2_formula_56(self):
        """Тест формулы 56: Выбросы CO2 от осушения лесных почв."""
        # CO2_organic = A × EF × CARBON_TO_CO2_FACTOR
        area = 100.0
        ef = 0.71

        result = self.calc.calculate_drained_forest_co2(area, ef)

        expected = 100.0 * 0.71 * CARBON_TO_CO2_FACTOR
        assert abs(result - expected) < 0.1

    def test_calculate_drained_forest_n2o_formula_57(self):
        """Тест формулы 57: Выбросы N2O от осушения лесных почв."""
        # N2O_organic = A × EF × 44/28 / 1000
        area = 100.0
        ef = 1.71

        result = self.calc.calculate_drained_forest_n2o(area, ef)

        expected = 100.0 * 1.71 * (44 / 28) / 1000
        assert abs(result - expected) < 0.001
        assert abs(result - 0.26871) < 0.001

    def test_calculate_drained_forest_ch4_formula_58(self):
        """Тест формулы 58: Выбросы CH4 от осушения лесных почв."""
        # CH4_organic = A × (1 - Frac_ditch) × EF_land + A × Frac_ditch × EF_ditch
        area = 100.0
        frac_ditch = 0.025
        ef_land = 4.5
        ef_ditch = 217.0

        result = self.calc.calculate_drained_forest_ch4(
            area, frac_ditch, ef_land, ef_ditch
        )

        expected = 100.0 * ((1 - 0.025) * 4.5 + 0.025 * 217.0)
        assert abs(result - expected) < 0.2

    def test_calculate_forest_fire_emissions_formula_59(self):
        """Тест формулы 59: Выбросы ПГ от лесных пожаров."""
        # L_пожар = A × MB × C_f × G_ef × 10^-3
        area = 100.0
        fuel_mass = 50.0
        combustion_factor = 0.43
        emission_factor = 1569.0  # CO2

        result = self.calc.calculate_forest_fire_emissions(
            area, fuel_mass, combustion_factor, emission_factor
        )

        expected = 100.0 * 50.0 * 0.43 * 1569.0 * 0.001
        assert abs(result - expected) < 0.01
        assert abs(result - 3373.35) < 0.01


class TestProtectiveForestCalculator:
    """Тесты для ProtectiveForestCalculator (формулы 60-74)."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.calc = ProtectiveForestCalculator()

    def test_calculate_protective_biomass_dynamics_formula_60(self):
        """Тест формулы 60: Динамика углерода в биомассе защитных насаждений."""
        # CPA_ij1 = SA_j1 × CPAM_ij
        area = 50.0  # га
        mean_carbon = 25.0  # т C/га

        result = self.calc.calculate_protective_biomass_dynamics(area, mean_carbon)

        expected = 50.0 * 25.0
        assert result == expected
        assert result == 1250.0

    def test_calculate_protective_biomass_sum_formula_61(self):
        """Тест формулы 61: Суммарный запас углерода в биомассе."""
        # CPA_ij = Σ CPA_ijl
        carbon_stocks = [1000.0, 1500.0, 800.0, 1200.0]

        result = self.calc.calculate_protective_biomass_sum(carbon_stocks)

        expected = sum(carbon_stocks)
        assert result == expected
        assert result == 4500.0

    def test_calculate_protective_biomass_absorption_formula_62(self):
        """Тест формулы 62: Поглощение углерода биомассой за год."""
        # CPAS_ij = CPA_(i+1)j - CPA_ij
        carbon_next_year = 5000.0
        carbon_current_year = 4500.0

        result = self.calc.calculate_protective_biomass_absorption(
            carbon_next_year, carbon_current_year
        )

        expected = 5000.0 - 4500.0
        assert result == expected
        assert result == 500.0  # т C/год

    def test_calculate_protective_deadwood_dynamics_formula_63(self):
        """Тест формулы 63: Динамика углерода в мертвом органическом веществе."""
        # CPD_ij1 = SD_j1 × CPDM_ij
        area = 50.0
        mean_deadwood_carbon = 3.0

        result = self.calc.calculate_protective_deadwood_dynamics(
            area, mean_deadwood_carbon
        )

        expected = 50.0 * 3.0
        assert result == expected
        assert result == 150.0

    def test_calculate_protective_deadwood_sum_formula_64(self):
        """Тест формулы 64: Суммарный запас углерода в мертвой древесине."""
        # CPD_ij = Σ CPD_ijl
        deadwood_stocks = [100.0, 150.0, 120.0]

        result = self.calc.calculate_protective_deadwood_sum(deadwood_stocks)

        expected = sum(deadwood_stocks)
        assert result == expected
        assert result == 370.0

    def test_calculate_protective_deadwood_accumulation_formula_65(self):
        """Тест формулы 65: Накопление углерода в мертвой древесине за год."""
        # CPDS_ij = CPD_(i+1)j - CPD_ij
        carbon_next = 400.0
        carbon_current = 370.0

        result = self.calc.calculate_protective_deadwood_accumulation(
            carbon_next, carbon_current
        )

        expected = 400.0 - 370.0
        assert result == expected
        assert result == 30.0

    def test_calculate_protective_litter_dynamics_formula_66(self):
        """Тест формулы 66: Динамика углерода в подстилке."""
        # CPL_ij1 = SL_j1 × CPLM_ij
        area = 50.0
        mean_litter_carbon = 2.5

        result = self.calc.calculate_protective_litter_dynamics(area, mean_litter_carbon)

        expected = 50.0 * 2.5
        assert result == expected
        assert result == 125.0

    def test_calculate_protective_litter_sum_formula_67(self):
        """Тест формулы 67: Суммарный запас углерода в подстилке."""
        # CPL_ij = Σ CPL_ijl
        litter_stocks = [100.0, 120.0, 110.0, 130.0]

        result = self.calc.calculate_protective_litter_sum(litter_stocks)

        expected = sum(litter_stocks)
        assert result == expected
        assert result == 460.0

    def test_calculate_protective_litter_accumulation_formula_68(self):
        """Тест формулы 68: Накопление углерода в подстилке за год."""
        # CPLS_ij = CPL_(i+1)j - CPL_ij
        litter_next = 480.0
        litter_current = 460.0

        result = self.calc.calculate_protective_litter_accumulation(
            litter_next, litter_current
        )

        expected = 480.0 - 460.0
        assert result == expected
        assert result == 20.0

    def test_calculate_protective_soil_dynamics_formula_69(self):
        """Тест формулы 69: Динамика углерода в почве насаждений."""
        # CPS_ij1 = SS_j1 × CPSM_ij
        area = 50.0
        mean_soil_carbon = 80.0

        result = self.calc.calculate_protective_soil_dynamics(area, mean_soil_carbon)

        expected = 50.0 * 80.0
        assert result == expected
        assert result == 4000.0

    def test_calculate_protective_soil_sum_formula_70(self):
        """Тест формулы 70: Суммарный запас углерода в почве."""
        # CPS_ij = Σ CPS_ijl
        soil_stocks = [3000.0, 3500.0, 4000.0, 4200.0]

        result = self.calc.calculate_protective_soil_sum(soil_stocks)

        expected = sum(soil_stocks)
        assert result == expected
        assert result == 14700.0

    def test_calculate_protective_soil_accumulation_formula_71(self):
        """Тест формулы 71: Накопление углерода в почве за год."""
        # CPSS_ij = CPS_(i+1)j - CPS_ij
        soil_next = 15000.0
        soil_current = 14700.0

        result = self.calc.calculate_protective_soil_accumulation(
            soil_next, soil_current
        )

        expected = 15000.0 - 14700.0
        assert result == expected
        assert result == 300.0

    def test_calculate_protective_total_accumulation_formula_72(self):
        """Тест формулы 72: Общее накопление углерода по всем пулам."""
        # CPS_ij = CPAS_ij + CPDS_ij + CPLS_ij + CPSS_ij
        biomass_acc = 500.0
        deadwood_acc = 30.0
        litter_acc = 20.0
        soil_acc = 300.0

        result = self.calc.calculate_protective_total_accumulation(
            biomass_acc, deadwood_acc, litter_acc, soil_acc
        )

        expected = 500.0 + 30.0 + 20.0 + 300.0
        assert result == expected
        assert result == 850.0

    def test_calculate_converted_land_co2_formula_73(self):
        """Тест формулы 73: Выбросы CO2 от осушенных почв переведенных земель."""
        # CO2_organic = A × EF × CARBON_TO_CO2_FACTOR
        area = 100.0
        ef = 0.71

        result = self.calc.calculate_converted_land_co2(area, ef)

        expected = 100.0 * 0.71 * CARBON_TO_CO2_FACTOR
        assert abs(result - expected) < 0.01

    def test_calculate_converted_land_n2o_formula_74(self):
        """Тест формулы 74: Выбросы N2O от осушенных почв переведенных земель."""
        # N2O_organic = A × EF × 44/28 / 1000
        area = 100.0
        ef = 1.71

        result = self.calc.calculate_converted_land_n2o(area, ef)

        expected = 100.0 * 1.71 * (44 / 28) / 1000
        assert abs(result - expected) < 0.001
