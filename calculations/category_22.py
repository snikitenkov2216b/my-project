# calculations/category_22.py - Модуль для расчетов по Категории 22.
# Инкапсулирует бизнес-логику для сжигания отходов.
# Код полностью соответствует формулам из Приказа Минприроды РФ от 27.05.2022 N 371.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

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
        self.CARBON_TO_CO2_FACTOR = 44 / 12

    def calculate_co2_emissions_solid_waste(self, waste_mass: float, dry_matter_fraction: float, carbon_fraction: float, fossil_carbon_fraction: float, oxidation_factor: float) -> float:
        """
        Рассчитывает выбросы CO2 от сжигания твердых отходов.
        
        Реализует Уравнение 3 из методических указаний.
        
        :param waste_mass: Масса сожженных твердых отходов (ISW), т/год.
        :param dry_matter_fraction: Доля сухого вещества в отходах (dm), доля.
        :param carbon_fraction: Доля углерода в сухом веществе (CF), доля.
        :param fossil_carbon_fraction: Доля ископаемого углерода в общем углероде (FCF), доля.
        :param oxidation_factor: Коэффициент окисления (OF), доля.
        :return: Масса выбросов CO2 в тоннах.
        """
        # E_CO2 = ISW * dm * CF * FCF * OF * (44/12)
        co2_emissions = waste_mass * dry_matter_fraction * carbon_fraction * fossil_carbon_fraction * oxidation_factor * self.CARBON_TO_CO2_FACTOR
        return co2_emissions

    def calculate_co2_emissions_multicomponent(self, total_waste_mass: float, waste_composition: list, oxidation_factor: float) -> float:
        """
        Рассчитывает выбросы CO2 от сжигания многокомпонентных отходов (например, ТКО).
        
        Реализует Уравнение 3.1 из методических указаний.

        :param total_waste_mass: Общая масса сожженных отходов (IWX), т/год.
        :param waste_composition: Список словарей состава отходов [{'type': str, 'fraction': float}]
        :param oxidation_factor: Коэффициент окисления (OF), доля.
        :return: Масса выбросов CO2 в тоннах.
        """
        sum_term = 0
        for component in waste_composition:
            component_data = self.data_service.table_20_2.get(component['type'], {})
            wf_x = component['fraction'] # Доля компонента x
            dm_x = component_data.get('dry_matter', 0.0) # Доля сухого вещества
            cf_x = component_data.get('total_c_dry', 0.0) # Доля углерода
            fcf_x = component_data.get('fossil_c_fraction', 0.0) # Доля ископаемого углерода
            sum_term += (wf_x * dm_x * cf_x * fcf_x)
            
        # E_CO2 = IWX * sum(WF_x * DM_x * CF_x * FCF_x * OF_x) * (44/12)
        # OF_x принимается одинаковым для всех компонентов в одной печи.
        co2_emissions = total_waste_mass * sum_term * oxidation_factor * self.CARBON_TO_CO2_FACTOR
        return co2_emissions

    def calculate_co2_emissions_liquid_waste(self, liquid_waste_mass: float, carbon_fraction: float, oxidation_factor: float) -> float:
        """
        Рассчитывает выбросы CO2 при инсинерации ископаемых жидких отходов.
        
        Реализует Уравнение 3.2 из методических указаний.

        :param liquid_waste_mass: Количество сожженных ископаемых жидких отходов (ILW), т/год.
        :param carbon_fraction: Доля углерода в жидких отходах (CLW), доля.
        :param oxidation_factor: Коэффициент окисления (OF), доля.
        :return: Масса выбросов CO2 в тоннах.
        """
        # E_CO2 = ILW * CLW * OF * (44/12)
        co2_emissions = liquid_waste_mass * carbon_fraction * oxidation_factor * self.CARBON_TO_CO2_FACTOR
        return co2_emissions

    def calculate_n2o_emissions_from_incineration(self, waste_mass: float, ef_n2o: float) -> float:
        """
        Рассчитывает выбросы N2O от сжигания отходов.
        
        Реализует Уравнение 3.3 из методических указаний.

        :param waste_mass: Количество сожженных отходов (IW), т/год (влажный вес).
        :param ef_n2o: Коэффициент выбросов N2O, кг N2O/т отходов.
        :return: Масса выбросов N2O в тоннах.
        """
        # E_N2O (т) = IW (т) * EF (кг/т) * 10^-3 (т/кг)
        # Методика использует множитель 10^-6 для перевода из кг в Гг, здесь сразу в тонны.
        n2o_emissions = waste_mass * ef_n2o * 10**-3
        return n2o_emissions