# calculations/category_7.py - Модуль для расчетов по Категории 7.
# Инкапсулирует бизнес-логику для производства извести.
# Код обновлен для полной реализации формул 7.1 и 7.2 из методики.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category7Calculator:
    """
    Класс-калькулятор для категории 7: "Производство извести".
    Предоставляет методы для расчета выбросов CO2 двумя способами:
    на основе расхода сырья или на основе производства извести.
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    def calculate_based_on_raw_materials(self, carbonates: list, lime_dust: dict) -> float:
        """
        Рассчитывает выбросы CO2 на основе данных о расходе карбонатного сырья.
        
        Реализует формулу 7.1 из методических указаний:
        E_CO2 = sum(M_j*EF_j*F_j) - sum(M_LD*W_j_LD*(1-F_LD)*EF_j)

        :param carbonates: Список словарей сырья. [{'name': str, 'mass': float, 'calcination_degree': float}]
        :param lime_dust: Словарь с данными о пыли. {'mass': float, 'carbonate_fractions': list, 'calcination_degree': float}
        :return: Масса выбросов CO2 в тоннах.
        """
        # Первое слагаемое: Выбросы от карбонатов
        emissions_from_carbonates = 0.0
        for carb in carbonates:
            carbonate_data = self.data_service.get_carbonate_data_table_6_1(carb['name'])
            if not carbonate_data:
                raise ValueError(f"Данные для карбоната '{carb['name']}' не найдены.")
            ef_co2 = carbonate_data.get('EF_CO2', 0.0)
            emissions_from_carbonates += carb['mass'] * ef_co2 * carb.get('calcination_degree', 1.0)

        # Второе слагаемое: Вычет на неразложившиеся карбонаты в пыли
        deduction_for_dust = 0.0
        if lime_dust and lime_dust.get('mass', 0) > 0:
            m_ld = lime_dust['mass']
            f_ld = lime_dust.get('calcination_degree', 1.0)
            # W_j_LD - доля исходного карбоната j в составе пыли
            for carb_fraction in lime_dust.get('carbonate_fractions', []):
                 carbonate_data = self.data_service.get_carbonate_data_table_6_1(carb_fraction['name'])
                 if not carbonate_data:
                     raise ValueError(f"Данные для карбоната '{carb_fraction['name']}' в пыли не найдены.")
                 ef_co2 = carbonate_data.get('EF_CO2', 0.0)
                 deduction_for_dust += m_ld * carb_fraction['fraction'] * (1 - f_ld) * ef_co2

        total_co2_emissions = emissions_from_carbonates - deduction_for_dust
        return total_co2_emissions

    def calculate_based_on_lime(self, lime_production: float, lime_composition: list, lime_dust: dict) -> float:
        """
        Рассчитывает выбросы CO2 на основе данных о производстве извести.
        
        Реализует формулу 7.2 из методических указаний:
        E_CO2 = LP * sum(W_i * EF_i) + M_LD * sum(W_i_LD * EF_i)

        :param lime_production: Масса произведенной извести, т.
        :param lime_composition: Список словарей состава извести. [{'oxide_name': 'CaO', 'fraction': float}, {'oxide_name': 'MgO', 'fraction': float}]
        :param lime_dust: Словарь с данными о пыли. {'mass': float, 'oxide_composition': list}
        :return: Масса выбросов CO2 в тоннах.
        """
        # Первое слагаемое: Выбросы от произведенной извести
        emissions_from_lime = 0.0
        for oxide in lime_composition:
            oxide_data = self.data_service.get_oxide_data_table_6_2(oxide['oxide_name'])
            if not oxide_data:
                raise ValueError(f"Данные для оксида '{oxide['oxide_name']}' не найдены.")
            ef_co2 = oxide_data.get('EF_CO2', 0.0)
            emissions_from_lime += lime_production * oxide['fraction'] * ef_co2

        # Второе слагаемое: Выбросы от оксидов в пыли
        emissions_from_dust = 0.0
        if lime_dust and lime_dust.get('mass', 0) > 0:
            m_ld = lime_dust['mass']
            for oxide in lime_dust.get('oxide_composition', []):
                oxide_data = self.data_service.get_oxide_data_table_6_2(oxide['oxide_name'])
                if not oxide_data:
                    raise ValueError(f"Данные для оксида '{oxide['oxide_name']}' в пыли не найдены.")
                ef_co2 = oxide_data.get('EF_CO2', 0.0)
                emissions_from_dust += m_ld * oxide['fraction'] * ef_co2
        
        total_co2_emissions = emissions_from_lime + emissions_from_dust
        return total_co2_emissions