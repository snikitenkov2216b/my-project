# calculations/absorption_agricultural.py
"""
Калькуляторы для расчета поглощения парниковых газов сельскохозяйственными угодьями.
Формулы 75-100 из Приказа Минприроды РФ от 27.05.2022 N 371.

ИСПРАВЛЕНИЯ:
- Обновлены значения GWP на актуальные AR5 IPCC (2014): CH4=28, N2O=265
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class CropData:
    """Данные о сельскохозяйственной культуре."""

    crop_type: str  # Тип культуры
    yield_value: float  # Урожайность, ц/га
    area: float  # Площадь, га
    carbon_content: float  # Содержание углерода, %


@dataclass
class LivestockData:
    """Данные о пастбищных животных."""

    animal_type: str  # Тип животного
    count: int  # Поголовье
    excretion_factor: float  # Коэффициент экскреции углерода
    grazing_time: float  # Время на пастбище, %


class AgriculturalLandCalculator:
    """Калькулятор для сельскохозяйственных угодий (формулы 75-90)."""

    # ИСПРАВЛЕНО: Актуальные значения GWP согласно AR5 IPCC (2014)
    GWP_VALUES = {
        "CH4": 28,  # Было: 25
        "N2O": 265,  # Было: 298
        "CO2": 1,
    }

    def calculate_drained_ch4_emissions(
        self,
        area: float,
        frac_ditch: float = 0.05,
        ef_land: float = 1.4,
        ef_ditch: float = 43.63,
    ) -> float:
        """
        Формула 75: Выбросы CH4 от осушенных органогенных почв.
        CH4_organic = A × (1 - Frac_ditch) × EF_land + A × Frac_ditch × EF_ditch

        :param area: Площадь осушенных почв, га
        :param frac_ditch: Доля канав
        :param ef_land: Коэффициент для земель, кг CH4/га/год
        :param ef_ditch: Коэффициент для канав, кг CH4/га/год
        :return: Выбросы CH4, кг/год
        """
        return area * ((1 - frac_ditch) * ef_land + frac_ditch * ef_ditch)

    def calculate_fire_emissions(
        self,
        area: float,
        biomass_mass: float,
        combustion_factor: float,
        emission_factor: float,
    ) -> float:
        """
        Формула 76: Выбросы ПГ от пожаров.
        L_пожар = A × MB × C_f × G_ef × 10^-3

        :param area: Площадь пожара, га
        :param biomass_mass: Масса биомассы, т/га
        :param combustion_factor: Коэффициент сгорания
        :param emission_factor: Коэффициент выбросов, г/кг
        :return: Выбросы, т
        """
        return area * biomass_mass * combustion_factor * emission_factor * 0.001

    def calculate_biomass_carbon_change(
        self, carbon_gain: float, carbon_loss: float
    ) -> float:
        """
        Формула 77: Изменение запасов углерода в биомассе.
        ΔC = ΔC_G - ΔC_L

        :param carbon_gain: Прирост углерода, т C/год
        :param carbon_loss: Потери углерода, т C/год
        :return: Изменение запасов, т C/год
        """
        return carbon_gain - carbon_loss

    def calculate_carbon_gain(self, carbon_per_ha: float, area_gain: float) -> float:
        """
        Формула 78: Прирост углерода.
        ΔC_G = C_gain × A_gain

        :param carbon_per_ha: Прирост углерода на га, т C/га/год
        :param area_gain: Площадь прироста, га
        :return: Общий прирост, т C/год
        """
        return carbon_per_ha * area_gain

    def calculate_carbon_loss(self, carbon_per_ha: float, area_loss: float) -> float:
        """
        Формула 79: Потери углерода.
        ΔC_L = C_loss × A_loss

        :param carbon_per_ha: Потери углерода на га, т C/га/год
        :param area_loss: Площадь потерь, га
        :return: Общие потери, т C/год
        """
        return carbon_per_ha * area_loss

    def calculate_mineral_soil_carbon_change(
        self,
        c_fertilizer: float,
        c_lime: float,
        c_plant: float,
        c_respiration: float,
        c_erosion: float,
    ) -> float:
        """
        Формула 80: Изменение запасов углерода в минеральных почвах.
        ΔC_минеральные = (Cfert + Clime + Cplant) - (Cresp + Cerosion)

        :param c_fertilizer: Углерод от удобрений, т C/год
        :param c_lime: Углерод от извести, т C/год
        :param c_plant: Углерод от растений, т C/год
        :param c_respiration: Потери от дыхания, т C/год
        :param c_erosion: Потери от эрозии, т C/год
        :return: Изменение запасов, т C/год
        """
        inputs = c_fertilizer + c_lime + c_plant
        outputs = c_respiration + c_erosion
        return inputs - outputs

    def calculate_fertilizer_carbon(
        self,
        organic_fertilizers: Dict[str, Tuple[float, float]],
        mineral_fertilizers: Dict[str, Tuple[float, float]],
    ) -> float:
        """
        Формула 81: Углерод от удобрений.
        Cfert = Σ(Орг_i × C_орг_i) + Σ(Мин_j × C_мин_j)

        :param organic_fertilizers: {тип: (количество, содержание_C)}
        :param mineral_fertilizers: {тип: (количество, коэффициент_C)}
        :return: Углерод от удобрений, т C/год
        """
        organic_c = sum(
            amount * c_content for amount, c_content in organic_fertilizers.values()
        )
        mineral_c = sum(
            amount * c_coef for amount, c_coef in mineral_fertilizers.values()
        )
        return organic_c + mineral_c

    def calculate_lime_carbon(self, lime_amount: float) -> float:
        """
        Формула 82: Углерод от извести.
        Clime = Lime × 8.75/100

        :param lime_amount: Количество извести, т/год
        :return: Углерод от извести, т C/год
        """
        return lime_amount * 0.0875

    def calculate_plant_residue_carbon(
        self, aboveground_carbon: float, underground_carbon: float
    ) -> float:
        """
        Формула 83: Углерод от растительных остатков.
        Cplant = C_ab + C_un

        :param aboveground_carbon: Углерод надземных остатков, т C/год
        :param underground_carbon: Углерод подземных остатков, т C/год
        :return: Общий углерод от растений, т C/год
        """
        return aboveground_carbon + underground_carbon

    def calculate_crop_residue_carbon(
        self, crops: List[CropData], a_coef: Dict[str, float], b_coef: Dict[str, float]
    ) -> float:
        """
        Формула 84: Углерод от остатков культур.
        C_ab или C_un = Σ((a_i × Y_i + b_i) × C_i) × S_i

        :param crops: Данные о культурах
        :param a_coef: Коэффициенты a для культур
        :param b_coef: Коэффициенты b для культур
        :return: Углерод от остатков, т C/год
        """
        total_carbon = 0
        for crop in crops:
            a = a_coef.get(crop.crop_type, 0.3)
            b = b_coef.get(crop.crop_type, 3.0)
            carbon = (a * crop.yield_value + b) * crop.carbon_content * crop.area
            total_carbon += carbon
        return total_carbon

    def calculate_erosion_losses(self, area: float, erosion_factor: float) -> float:
        """
        Формула 85: Потери углерода от эрозии.
        Cerosion = A × EFerosion

        :param area: Площадь, га
        :param erosion_factor: Коэффициент эрозии, т C/га/год
        :return: Потери от эрозии, т C/год
        """
        return area * erosion_factor

    def calculate_soil_respiration(
        self,
        area: float,
        co2_emission_rate: float,
        vegetation_period: float,
        conversion_factor: float = 0.6,
    ) -> float:
        """
        Формула 86: Потери углерода от дыхания почвы.
        Cresp = Σ((Area_i × AC_CO2i × Veg × 0.6 × 1.43) / 100) × 12/44

        :param area: Площадь, га
        :param co2_emission_rate: Скорость эмиссии CO2, мг CO2/м²/час
        :param vegetation_period: Вегетационный период, дни
        :param conversion_factor: Коэффициент конверсии
        :return: Потери от дыхания, т C/год
        """
        co2_emission = (
            area * co2_emission_rate * vegetation_period * conversion_factor * 1.43
        ) / 100
        return co2_emission * (12 / 44)

    def calculate_organic_soil_co2(self, area: float, ef: float = 5.9) -> float:
        """
        Формула 87: Выбросы CO2 от органогенных почв.
        CO2_organic = A × EF_C_CO2 × 44/12

        :param area: Площадь, га
        :param ef: Коэффициент выброса, т C/га/год
        :return: Выбросы CO2, т/год
        """
        return area * ef * (44 / 12)

    def calculate_organic_soil_n2o(self, area: float, ef: float = 7.0) -> float:
        """
        Формула 88: Выбросы N2O от органогенных почв.
        N2O_organic = A × EF_N_N2O × 44/28

        :param area: Площадь, га
        :param ef: Коэффициент выброса, кг N-N2O/га/год
        :return: Выбросы N2O, т/год
        """
        return area * ef * (44 / 28) / 1000

    def calculate_organic_soil_ch4(
        self,
        area: float,
        frac_ditch: float = 0.5,
        ef_land: float = 0.0,
        ef_ditch: float = 1165,
    ) -> float:
        """
        Формула 89: Выбросы CH4 от органогенных почв.
        CH4_organic = A × (1 - Frac_ditch) × EF_land + A × Frac_ditch × EF_ditch

        :param area: Площадь, га
        :param frac_ditch: Доля канав
        :param ef_land: Коэффициент для земель, кг CH4/га/год
        :param ef_ditch: Коэффициент для канав, кг CH4/га/год
        :return: Выбросы CH4, кг/год
        """
        return area * ((1 - frac_ditch) * ef_land + frac_ditch * ef_ditch)

    def calculate_agricultural_fire_emissions(
        self, area: float, biomass: float, combustion: float, emission_factor: float
    ) -> float:
        """
        Формула 90: Выбросы от пожаров на сельхозземлях.
        L_пожар = A × MB × C_f × G_ef × 10^-3

        :param area: Площадь, га
        :param biomass: Масса биомассы, т/га
        :param combustion: Коэффициент сгорания
        :param emission_factor: Коэффициент выбросов, г/кг
        :return: Выбросы, т
        """
        return area * biomass * combustion * emission_factor * 0.001


class LandConversionCalculator:
    """Калькулятор для конверсии земель (формулы 91-100)."""

    # ИСПРАВЛЕНО: Актуальные значения GWP согласно AR5 IPCC (2014)
    GWP_VALUES = {
        "CH4": 28,  # Было: 25
        "N2O": 265,  # Было: 298
        "CO2": 1,
    }

    def calculate_conversion_carbon_change(
        self,
        carbon_after: List[float],
        carbon_before: List[float],
        conversion_area: float,
        period: float,
    ) -> float:
        """
        Формула 91: Изменение запасов углерода при конверсии.
        ΔC_конверсия = (Σ C_после_i - C_до_i) × ΔA_в_пахотные / D

        :param carbon_after: Запасы углерода после конверсии по категориям
        :param carbon_before: Запасы углерода до конверсии по категориям
        :param conversion_area: Площадь конверсии, га
        :param period: Период конверсии, лет
        :return: Изменение запасов, т C/год
        """
        if period <= 0:
            raise ValueError("Период должен быть больше 0")

        total_change = sum(carbon_after) - sum(carbon_before)
        return total_change * conversion_area / period

    def calculate_converted_land_co2(self, area: float, ef: float = 5.9) -> float:
        """
        Формула 92: Выбросы CO2 от осушенных почв переведенных земель.
        CO2_organic = A × EF_C_CO2 × 44/12

        :param area: Площадь, га
        :param ef: Коэффициент выброса, т C/га/год
        :return: Выбросы CO2, т/год
        """
        return area * ef * (44 / 12)

    def calculate_converted_land_n2o(self, area: float, ef: float = 7.0) -> float:
        """
        Формула 93: Выбросы N2O от осушенных почв переведенных земель.
        N2O_organic = A × EF_N_N2O × 44/28

        :param area: Площадь, га
        :param ef: Коэффициент выброса, кг N/га/год
        :return: Выбросы N2O, т/год
        """
        return area * ef * (44 / 28) / 1000

    def calculate_converted_land_ch4(
        self,
        area: float,
        frac_ditch: float = 0.5,
        ef_land: float = 0.0,
        ef_ditch: float = 1165,
    ) -> float:
        """
        Формула 94: Выбросы CH4 от осушенных почв переведенных земель.
        CH4_organic = A × (1 - Frac_ditch) × EF_land + A × Frac_ditch × EF_ditch

        :param area: Площадь, га
        :param frac_ditch: Доля канав
        :param ef_land: Коэффициент для земель, кг CH4/га/год
        :param ef_ditch: Коэффициент для канав, кг CH4/га/год
        :return: Выбросы CH4, кг/год
        """
        return area * ((1 - frac_ditch) * ef_land + frac_ditch * ef_ditch)

    def calculate_conversion_fire_emissions(
        self, area: float, biomass: float, combustion: float, emission_factor: float
    ) -> float:
        """
        Формула 95: Выбросы от пожаров при конверсии земель.
        L_пожар = A × MB × C_f × G_ef × 10^-3

        :param area: Площадь, га
        :param biomass: Масса биомассы, т/га
        :param combustion: Коэффициент сгорания
        :param emission_factor: Коэффициент выбросов, г/кг
        :return: Выбросы, т
        """
        return area * biomass * combustion * emission_factor * 0.001

    def to_co2_equivalent(self, gas_amount: float, gas_type: str) -> float:
        """
        Перевод газа в CO2-эквивалент с использованием актуальных GWP.

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
