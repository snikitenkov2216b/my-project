# calculations/absorption_permanent_forest.py
"""
Калькуляторы для расчета поглощения парниковых газов постоянными лесными землями.
Формулы 27-74 из Приказа Минприроды РФ от 27.05.2022 N 371.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import math


@dataclass
class ForestStandData:
    """Данные о древостое по группам возраста."""

    age_group: int  # Группа возраста (индекс i)
    species: str  # Преобладающая порода (индекс j)
    volume: float  # Запас древесины, м³/га (V_ij)
    area: float  # Площадь, га (S_ij)
    age_interval: float  # Возрастной интервал, лет (TI_ij)


class PermanentForestCalculator:
    """Калькулятор для постоянных лесных земель (формулы 27-55)."""

    def calculate_biomass_carbon_stock(
        self, volume: float, conversion_factor: float
    ) -> float:
        """
        Формула 27: Запас углерода в биомассе древостоев.
        CP_ij = V_ij × KP_ij

        :param volume: Запас древесины, м³
        :param conversion_factor: Коэффициент перевода (KP_ij)
        :return: Запас углерода, т C
        """
        return volume * conversion_factor

    def calculate_mean_carbon_per_hectare(
        self, carbon_stock: float, area: float
    ) -> float:
        """
        Формула 28: Средний запас углерода на гектар.
        MCP_ij = CP_ij / S_ij

        :param carbon_stock: Запас углерода, т C
        :param area: Площадь, га
        :return: Средний запас, т C/га
        """
        if area <= 0:
            raise ValueError("Площадь должна быть больше 0")
        return carbon_stock / area

    def calculate_carbon_absorption_rate(
        self,
        mcp_current: float,
        mcp_prev: float,
        mcp_next: float,
        ti_prev: float,
        ti_current: float,
        ti_next: float,
    ) -> float:
        """
        Формула 29: Скорость абсорбции углерода.
        MAbP_ij = (MCP_ij - MCP_i-1,j)/(TI_i-1,j + TI_ij) +
                  (MCP_i+1,j - MCP_ij)/(TI_ij + TI_i+1,j)

        :param mcp_current: Текущий средний запас C
        :param mcp_prev: Предыдущий средний запас C
        :param mcp_next: Следующий средний запас C
        :param ti_prev: Предыдущий возрастной интервал
        :param ti_current: Текущий возрастной интервал
        :param ti_next: Следующий возрастной интервал
        :return: Скорость абсорбции, т C/га/год
        """
        term1 = (mcp_current - mcp_prev) / (ti_prev + ti_current)
        term2 = (mcp_next - mcp_current) / (ti_current + ti_next)
        return term1 + term2

    def calculate_total_absorption(self, area: float, absorption_rate: float) -> float:
        """
        Формула 30: Общая абсорбция углерода.
        AbP_ij = S_ij × MAbP_ij

        :param area: Площадь, га
        :param absorption_rate: Скорость абсорбции, т C/га/год
        :return: Общая абсорбция, т C/год
        """
        return area * absorption_rate

    def calculate_annual_disturbance_rate_fire(
        self, burned_area: float, rotation_period: float
    ) -> float:
        """
        Формула 31: Годичный темп пожарных нарушений.
        ASF = SB / TRB

        :param burned_area: Площадь пожаров за период, га
        :param rotation_period: Период ротации, лет
        :return: Годичный темп, га/год
        """
        if rotation_period <= 0:
            raise ValueError("Период ротации должен быть больше 0")
        return burned_area / rotation_period

    def calculate_annual_disturbance_rate_harvest(
        self, harvested_area: float, rotation_period: float
    ) -> float:
        """
        Формула 32: Годичный темп рубок.
        ASH = SC / TRC

        :param harvested_area: Площадь рубок за период, га
        :param rotation_period: Период ротации, лет
        :return: Годичный темп, га/год
        """
        if rotation_period <= 0:
            raise ValueError("Период ротации должен быть больше 0")
        return harvested_area / rotation_period

    def calculate_harvest_biomass_loss(
        self, annual_harvest_area: float, mean_carbon_stock: float, mean_area: float
    ) -> float:
        """
        Формула 33: Потери биомассы при сплошных рубках.
        LsPH = ASH × CP_m / S_m

        :param annual_harvest_area: Годичная площадь рубок, га/год
        :param mean_carbon_stock: Средний запас углерода, т C
        :param mean_area: Средняя площадь, га
        :return: Потери углерода, т C/год
        """
        if mean_area <= 0:
            raise ValueError("Площадь должна быть больше 0")
        return annual_harvest_area * mean_carbon_stock / mean_area

    def calculate_fire_biomass_loss(
        self, annual_fire_area: float, mean_carbon_stock: float, mean_area: float
    ) -> float:
        """
        Формула 34: Потери биомассы при пожарах.
        LsPF = ASF × CP_a / S_a

        :param annual_fire_area: Годичная площадь пожаров, га/год
        :param mean_carbon_stock: Средний запас углерода, т C
        :param mean_area: Средняя площадь, га
        :return: Потери углерода, т C/год
        """
        if mean_area <= 0:
            raise ValueError("Площадь должна быть больше 0")
        return annual_fire_area * mean_carbon_stock / mean_area

    def calculate_biomass_budget(
        self, absorption: float, harvest_loss: float, fire_loss: float
    ) -> float:
        """
        Формула 35: Годичный бюджет углерода биомассы.
        BP = AbP - LsPH - LsPF

        :param absorption: Абсорбция углерода, т C/год
        :param harvest_loss: Потери от рубок, т C/год
        :param fire_loss: Потери от пожаров, т C/год
        :return: Бюджет углерода, т C/год
        """
        return absorption - harvest_loss - fire_loss

    def calculate_deadwood_carbon_stock(
        self, volume: float, conversion_factor: float
    ) -> float:
        """
        Формула 36: Запас углерода в мертвой древесине.
        CD_ij = V_ij × KD_ij

        :param volume: Запас древесины, м³
        :param conversion_factor: Коэффициент перевода для мертвой древесины
        :return: Запас углерода, т C
        """
        return volume * conversion_factor

    def calculate_litter_carbon_stock(self, area: float, litter_factor: float) -> float:
        """
        Формула 43: Запас углерода в подстилке.
        CL_ij = S_ij × KL_ij

        :param area: Площадь, га
        :param litter_factor: Коэффициент углерода в подстилке, т C/га
        :return: Запас углерода в подстилке, т C
        """
        return area * litter_factor

    def calculate_soil_carbon_stock(self, area: float, soil_factor: float) -> float:
        """
        Формула 49: Запас углерода в почве.
        CS_ij = S_ij × KS_ij

        :param area: Площадь, га
        :param soil_factor: Коэффициент углерода в почве, т C/га
        :return: Запас углерода в почве, т C
        """
        return area * soil_factor

    def calculate_soil_absorption(
        self,
        mcs_current: float,
        mcs_prev: float,
        mcs_next: float,
        ti_prev: float,
        ti_current: float,
        ti_next: float,
    ) -> float:
        """
        Формула 50: Абсорбция углерода почвой.
        MAbS_ij = (MCS_ij - MCS_i-1,j)/(TI_i-1,j - TI_ij) +
                  (MCS_i+1,j - MCS_ij)/(TI_ij - TI_i+1,j)
        """
        term1 = (mcs_current - mcs_prev) / (ti_prev - ti_current)
        term2 = (mcs_next - mcs_current) / (ti_current - ti_next)
        return term1 + term2

    def calculate_soil_harvest_loss(
        self,
        harvest_area: float,
        mean_soil_carbon: float,
        mean_area: float,
        initial_soil_carbon: float,
    ) -> float:
        """
        Формула 52: Потери углерода почвы при рубках.
        LsSH = ASH × (CS_m/S_m - MCS_0m)
        """
        if mean_area <= 0:
            raise ValueError("Площадь должна быть больше 0")
        return harvest_area * (mean_soil_carbon / mean_area - initial_soil_carbon)

    def calculate_soil_fire_loss(
        self,
        fire_area: float,
        mean_soil_carbon: float,
        mean_area: float,
        initial_soil_carbon: float,
    ) -> float:
        """
        Формула 53: Потери углерода почвы при пожарах.
        LsSF = ASF × (CS_a/S_a - MCS_0a)
        """
        if mean_area <= 0:
            raise ValueError("Площадь должна быть больше 0")
        return fire_area * (mean_soil_carbon / mean_area - initial_soil_carbon)

    def calculate_soil_budget(
        self, absorption: float, harvest_loss: float, fire_loss: float
    ) -> float:
        """
        Формула 54: Годичный бюджет углерода почвы.
        BS = AbS - LsSH - LsSF
        """
        return absorption - harvest_loss - fire_loss

    def calculate_total_budget(
        self,
        biomass_budget: float,
        deadwood_budget: float,
        litter_budget: float,
        soil_budget: float,
    ) -> float:
        """
        Формула 55: Суммарный бюджет углерода.
        BT = BP + BD + BL + BS
        """
        return biomass_budget + deadwood_budget + litter_budget + soil_budget

    def calculate_drained_forest_co2(self, area: float, ef: float = 0.71) -> float:
        """
        Формула 56: Выбросы CO2 от осушения лесных почв.
        CO2_organic = A × EF × 44/12

        :param area: Площадь осушенных почв, га
        :param ef: Коэффициент выброса, т C/га/год
        :return: Выбросы CO2, т/год
        """
        return area * ef * (44 / 12)

    def calculate_drained_forest_n2o(self, area: float, ef: float = 1.71) -> float:
        """
        Формула 57: Выбросы N2O от осушения лесных почв.
        N2O_organic = A × EF × 44/28

        :param area: Площадь осушенных почв, га
        :param ef: Коэффициент выброса, кг N/га/год
        :return: Выбросы N2O, т/год
        """
        return area * ef * (44 / 28) / 1000

    def calculate_drained_forest_ch4(
        self,
        area: float,
        frac_ditch: float = 0.025,
        ef_land: float = 4.5,
        ef_ditch: float = 217,
    ) -> float:
        """
        Формула 58: Выбросы CH4 от осушения лесных почв.
        CH4_organic = A × (1 - Frac_ditch) × EF_land + A × Frac_ditch × EF_ditch
        """
        return area * ((1 - frac_ditch) * ef_land + frac_ditch * ef_ditch)

    def calculate_forest_fire_emissions(
        self,
        area: float,
        fuel_mass: float,
        combustion_factor: float,
        emission_factor: float,
    ) -> float:
        """
        Формула 59: Выбросы ПГ от лесных пожаров.
        L_пожар = A × MB × C_f × G_ef × 10^-3

        :param area: Площадь пожара, га
        :param fuel_mass: Масса топлива, т/га
        :param combustion_factor: Коэффициент сгорания
        :param emission_factor: Коэффициент выбросов, г/кг
        :return: Выбросы, т
        """
        return area * fuel_mass * combustion_factor * emission_factor * 0.001


class ProtectiveForestCalculator:
    """Калькулятор для защитных насаждений (формулы 60-74)."""

    def calculate_protective_biomass_dynamics(
        self, area: float, mean_carbon: float
    ) -> float:
        """
        Формула 60: Динамика углерода в биомассе защитных насаждений.
        CPA_ij1 = SA_j1 × CPAM_ij

        :param area: Площадь насаждений, га
        :param mean_carbon: Средний запас углерода, т C/га
        :return: Суммарный запас углерода, т C
        """
        return area * mean_carbon

    def calculate_protective_biomass_sum(self, carbon_stocks: List[float]) -> float:
        """
        Формула 61: Суммарный запас углерода в биомассе.
        CPA_ij = Σ CPA_ijl

        :param carbon_stocks: Список запасов углерода по годам создания
        :return: Суммарный запас, т C
        """
        return sum(carbon_stocks)

    def calculate_protective_biomass_absorption(
        self, carbon_next_year: float, carbon_current_year: float
    ) -> float:
        """
        Формула 62: Поглощение углерода биомассой за год.
        CPAS_ij = CPA_(i+1)j - CPA_ij

        :param carbon_next_year: Запас углерода в следующем году, т C
        :param carbon_current_year: Запас углерода в текущем году, т C
        :return: Годичное поглощение, т C/год
        """
        return carbon_next_year - carbon_current_year

    def calculate_protective_deadwood_dynamics(
        self, area: float, mean_deadwood_carbon: float
    ) -> float:
        """
        Формула 63: Динамика углерода в мертвом органическом веществе.
        CPD_ij1 = SD_j1 × CPDM_ij
        """
        return area * mean_deadwood_carbon

    def calculate_protective_deadwood_sum(self, deadwood_stocks: List[float]) -> float:
        """
        Формула 64: Суммарный запас углерода в мертвой древесине.
        CPD_ij = Σ CPD_ijl
        """
        return sum(deadwood_stocks)

    def calculate_protective_deadwood_accumulation(
        self, carbon_next: float, carbon_current: float
    ) -> float:
        """
        Формула 65: Накопление углерода в мертвой древесине за год.
        CPDS_ij = CPD_(i+1)j - CPD_ij
        """
        return carbon_next - carbon_current

    def calculate_protective_litter_dynamics(
        self, area: float, mean_litter_carbon: float
    ) -> float:
        """
        Формула 66: Динамика углерода в подстилке.
        CPL_ij1 = SL_j1 × CPLM_ij
        """
        return area * mean_litter_carbon

    def calculate_protective_litter_sum(self, litter_stocks: List[float]) -> float:
        """
        Формула 67: Суммарный запас углерода в подстилке.
        CPL_ij = Σ CPL_ijl
        """
        return sum(litter_stocks)

    def calculate_protective_litter_accumulation(
        self, litter_next: float, litter_current: float
    ) -> float:
        """
        Формула 68: Накопление углерода в подстилке за год.
        CPLS_ij = CPL_(i+1)j - CPL_ij
        """
        return litter_next - litter_current

    def calculate_protective_soil_dynamics(
        self, area: float, mean_soil_carbon: float
    ) -> float:
        """
        Формула 69: Динамика углерода в почве насаждений.
        CPS_ij1 = SS_j1 × CPSM_ij
        """
        return area * mean_soil_carbon

    def calculate_protective_soil_sum(self, soil_stocks: List[float]) -> float:
        """
        Формула 70: Суммарный запас углерода в почве.
        CPS_ij = Σ CPS_ijl
        """
        return sum(soil_stocks)

    def calculate_protective_soil_accumulation(
        self, soil_next: float, soil_current: float
    ) -> float:
        """
        Формула 71: Накопление углерода в почве за год.
        CPSS_ij = CPS_(i+1)j - CPS_ij
        """
        return soil_next - soil_current

    def calculate_protective_total_accumulation(
        self,
        biomass_acc: float,
        deadwood_acc: float,
        litter_acc: float,
        soil_acc: float,
    ) -> float:
        """
        Формула 72: Общее накопление углерода по всем пулам.
        CPS_ij = CPAS_ij + CPDS_ij + CPLS_ij + CPSS_ij
        """
        return biomass_acc + deadwood_acc + litter_acc + soil_acc

    def calculate_converted_land_co2(self, area: float, ef: float = 0.71) -> float:
        """
        Формула 73: Выбросы CO2 от осушенных почв переведенных земель.
        CO2_organic = A × EF × 44/12
        """
        return area * ef * (44 / 12)

    def calculate_converted_land_n2o(self, area: float, ef: float = 1.71) -> float:
        """
        Формула 74: Выбросы N2O от осушенных почв переведенных земель.
        N2O_organic = A × EF × 44/28
        """
        return area * ef * (44 / 28) / 1000
