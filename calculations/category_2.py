# calculations/category_2.py - Модуль для расчетов по Категории 2.
# Код обновлен с добавлением валидации входных данных.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category2Calculator:
    """
    Класс-калькулятор для категории 2: "Сжигание в факелах".
    Предоставляет методы для расчета выбросов CO2 и CH4.
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к таблицам с коэффициентами.
        """
        self.data_service = data_service

    def calculate_ef_co2(self, gas_composition: list, combustion_inefficiency_factor: float, gas_density: float, by_mass=False) -> float:
        """
        Рассчитывает коэффициент выбросов CO2 (EF_CO2) на основе компонентного состава.
        Реализует формулы 2.2 (по объему) и 2.3 (по массе).

        :param gas_composition: Список словарей компонентов газа.
               Для расчета по объему: [{'name': str, 'volume_fraction': float, 'carbon_atoms': int}]
               Для расчета по массе: [{'name': str, 'mass_fraction': float, 'carbon_atoms': int, 'molar_mass': float}]
        :param combustion_inefficiency_factor: Коэффициент недожога (CF), доля.
        :param gas_density: Плотность газовой смеси, кг/м3 (требуется только для расчета по массе).
        :param by_mass: Флаг, указывающий, что расчет ведется по массовым долям (формула 2.3).
        :return: Коэффициент выбросов, т CO2/тыс. м3.
        """
        molar_mass_co2 = 44.011
        rho_co2_standard = self.data_service.get_density_data_table_1_2()['rho_CO2']

        if not by_mass:
            # Формула 2.2 (по объему)
            w_co2 = next((comp.get('volume_fraction', 0.0) for comp in gas_composition if comp['name'] == 'CO2'), 0.0)
            sum_term = sum(
                (comp.get('volume_fraction', 0.0) * comp.get('carbon_atoms', 0))
                for comp in gas_composition if comp['name'] != 'CO2'
            )
            # EF = (W_CO2 + sum(W_i * n_C_i) * (1 - CF)) * rho_CO2 * 10^-2
            ef_co2 = (w_co2 + sum_term * (1 - combustion_inefficiency_factor)) * rho_co2_standard * 10**-2
        else:
            # Формула 2.3 (по массе)
            if gas_density <= 0:
                raise ValueError("Плотность газа для расчета по массе должна быть больше нуля.")
            w_co2 = next((comp.get('mass_fraction', 0.0) for comp in gas_composition if comp['name'] == 'CO2'), 0.0)
            sum_term = sum(
                ((comp.get('mass_fraction', 0.0) * comp.get('carbon_atoms', 0) * molar_mass_co2) / comp.get('molar_mass', 1))
                for comp in gas_composition if comp['name'] != 'CO2'
            )
            # EF = (W_CO2 + sum(...) * (1 - CF)) * rho_gas * 10^-2
            ef_co2 = (w_co2 + sum_term * (1 - combustion_inefficiency_factor)) * gas_density * 10**-2
        
        return ef_co2

    def calculate_ef_ch4(self, ch4_fraction: float, combustion_inefficiency_factor: float, by_mass=False) -> float:
        """
        Рассчитывает коэффициент выбросов CH4 (EF_CH4) на основе содержания метана.
        Реализует формулы 2.4 (по объему) и 2.5 (по массе).

        :param ch4_fraction: Доля метана (CH4) в смеси (объемная или массовая), %.
        :param combustion_inefficiency_factor: Коэффициент недожога (CF), доля.
        :param by_mass: Флаг, указывающий, что расчет ведется по массовой доле (формула 2.5).
        :return: Коэффициент выбросов, т CH4/тыс. м3 (по объему) или т CH4/т (по массе).
        """
        if not by_mass:
            # Формула 2.4 (по объему)
            rho_ch4_standard = self.data_service.get_density_data_table_1_2()['rho_CH4']
            # EF = W_CH4 * CF * rho_CH4 * 10^-2
            ef_ch4 = ch4_fraction * combustion_inefficiency_factor * rho_ch4_standard * 10**-2
        else:
            # Формула 2.5 (по массе)
            # EF = W_CH4 * CF * 10^-2
            ef_ch4 = ch4_fraction * combustion_inefficiency_factor * 10**-2
        
        return ef_ch4

    def calculate_emissions_with_default_factors(self, gas_type: str, consumption: float, unit: str) -> dict:
        """
        Рассчитывает выбросы CO2 и CH4, используя стандартные коэффициенты из Таблицы 2.1.
        Реализует формулу 2.1.

        :param gas_type: Наименование вида сжигаемого газа.
        :param consumption: Расход газа в указанных единицах.
        :param unit: Единица измерения расхода ('тонна' или 'тыс. м3').
        :return: Словарь с массами выбросов CO2 и CH4 в тоннах.
        """
        if consumption < 0:
            raise ValueError("Расход газа не может быть отрицательным.")

        gas_data = self.data_service.get_flare_gas_data_table_2_1(gas_type)
        if not gas_data:
            raise ValueError(f"Данные для газа '{gas_type}' не найдены в таблице 2.1.")

        if unit == 'тонна':
            ef_co2 = gas_data.get('EF_CO2_t')
            ef_ch4 = gas_data.get('EF_CH4_t')
        elif unit == 'тыс. м3':
            ef_co2 = gas_data.get('EF_CO2_m3')
            ef_ch4 = gas_data.get('EF_CH4_m3')
        else:
            raise ValueError(f"Некорректные единицы измерения: {unit}")

        if ef_co2 is None or ef_ch4 is None:
             raise ValueError(f"Для газа '{gas_type}' отсутствуют необходимые коэффициенты выбросов.")

        co2_emissions = consumption * ef_co2
        ch4_emissions = consumption * ef_ch4

        return {'co2': co2_emissions, 'ch4': ch4_emissions}