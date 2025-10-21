# calculations/category_22.py - Модуль для расчетов по Категории 22.
# Код обновлен для использования централизованных констант и валидации.
# Комментарии на русском. Поддержка UTF-8.

from data_models_extended import DataService
from config import CARBON_TO_CO2_FACTOR # ИМПОРТ

class Category22Calculator:
    """
    Класс-калькулятор для категории 22: "Сжигание отходов".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service
        self.CARBON_TO_CO2_FACTOR = CARBON_TO_CO2_FACTOR

    def calculate_co2_emissions_solid_waste(self, waste_mass: float, dm: float, cf: float, fcf: float, of: float) -> float:
        """
        Рассчитывает выбросы CO2 от сжигания твердых отходов (общий метод).
        Реализует формулу 3 из методических указаний.

        :param waste_mass: Общая масса сожженных отходов, т/год.
        :param dm: Доля сухого вещества в отходах.
        :param cf: Доля углерода в сухом веществе.
        :param fcf: Доля ископаемого углерода в общем углероде.
        :param of: Коэффициент полноты сгорания.
        :return: Масса выбросов CO2 в тоннах.
        """
        if waste_mass < 0:
            raise ValueError("Масса отходов не может быть отрицательной.")
        if not all(0 <= val <= 1 for val in [dm, cf, fcf, of]):
            raise ValueError("Все доли (dm, cf, fcf, of) должны быть в диапазоне от 0 до 1.")
            
        co2_emissions = waste_mass * dm * cf * fcf * of * self.CARBON_TO_CO2_FACTOR
        return co2_emissions

    def calculate_co2_emissions_multicomponent(self, total_waste_mass: float, composition: list, of: float) -> float:
        """
        Рассчитывает выбросы CO2 от сжигания многокомпонентных отходов (например, ТКО).
        Реализует формулу 3.1.

        :param total_waste_mass: Общая масса сожженных отходов, т/год.
        :param composition: Список словарей состава. [{'type': str, 'fraction': float}]
        :param of: Коэффициент полноты сгорания.
        :return: Масса выбросов CO2 в тоннах.
        """
        if total_waste_mass < 0 or not (0 <= of <= 1):
            raise ValueError("Масса отходов должна быть неотрицательной, а коэффициент окисления - от 0 до 1.")

        sum_term = 0
        for component in composition:
            comp_type = component['type']
            fraction = component['fraction'] # WF_i
            
            comp_data = self.data_service.table_20_2.get(comp_type)
            if not comp_data:
                raise ValueError(f"Данные для компонента '{comp_type}' не найдены в таблице 20.2.")

            dm = comp_data.get('dry_matter')
            total_c_dry = comp_data.get('total_c_dry')
            fcf = comp_data.get('fossil_c_fraction')

            if any(val is None for val in [dm, total_c_dry, fcf]):
                raise ValueError(f"Для компонента '{comp_type}' отсутствуют необходимые параметры (dm, total_c_dry или fcf).")
            
            sum_term += fraction * dm * total_c_dry * fcf

        co2_emissions = total_waste_mass * sum_term * of * self.CARBON_TO_CO2_FACTOR
        return co2_emissions

    def calculate_co2_emissions_liquid_waste(self, waste_mass: float, carbon_fraction: float, of: float) -> float:
        """
        Рассчитывает выбросы CO2 от сжигания ископаемых жидких отходов.
        Реализует формулу 3.2.

        :param waste_mass: Масса сожженных жидких отходов, т/год.
        :param carbon_fraction: Доля углерода в жидких отходах (CLW).
        :param of: Коэффициент полноты сгорания.
        :return: Масса выбросов CO2 в тоннах.
        """
        if waste_mass < 0 or not (0 <= carbon_fraction <= 1) or not (0 <= of <= 1):
            raise ValueError("Масса отходов должна быть неотрицательной, а доли - от 0 до 1.")

        co2_emissions = waste_mass * carbon_fraction * of * self.CARBON_TO_CO2_FACTOR
        return co2_emissions

    def calculate_n2o_emissions_from_incineration(self, waste_mass: float, emission_factor: float) -> float:
        """
        Рассчитывает выбросы N2O от сжигания отходов.
        Реализует формулу 3.3.

        :param waste_mass: Масса сожженных отходов (сырой вес), т/год.
        :param emission_factor: Коэффициент выбросов N2O, кг N2O/т отходов.
        :return: Масса выбросов N2O в тоннах.
        """
        if waste_mass < 0 or emission_factor < 0:
            raise ValueError("Масса отходов и коэффициент выбросов не могут быть отрицательными.")
            
        # E_N2O (т) = M_отх (т) * EF_N2O (кг/т) * 10^-3 (т/кг)
        n2o_emissions = waste_mass * emission_factor * 10**-3
        return n2o_emissions