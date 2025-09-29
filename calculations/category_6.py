# calculations/category_6.py - Модуль для расчетов по Категории 6.
# Инкапсулирует бизнес-логику для производства цемента.
# Код обновлен для полной реализации формул 6.1 и 6.2 из методики.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category6Calculator:
    """
    Класс-калькулятор для категории 6: "Производство цемента".
    Предоставляет методы для расчета выбросов CO2 двумя способами:
    на основе расхода сырья или на основе производства клинкера.
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service
        self.CARBON_TO_CO2_FACTOR = 3.664

    def _get_carbon_content(self, material_name: str) -> float:
        """
        Вспомогательный метод для получения содержания углерода (W_C) из Таблицы 1.1.
        
        :param material_name: Наименование материала/топлива.
        :return: Содержание углерода в т C / ед. изм.
        :raises ValueError: Если данные для материала не найдены.
        """
        data = self.data_service.get_fuel_data_table_1_1(material_name)
        if not data or 'W_C_ut' not in data:
            raise ValueError(f"Данные о содержании углерода для '{material_name}' не найдены в таблице 1.1.")
        return data['W_C_ut']

    def calculate_based_on_raw_materials(self, carbonates: list, cement_dust: dict, non_carbonate_materials: list) -> float:
        """
        Рассчитывает выбросы CO2 на основе данных о расходе карбонатного сырья.
        
        Реализует формулу 6.1 из методических указаний.
        E_CO2 = sum(M_j*EF_j*F_j) - sum(M_CD*W_j_CD*(1-F_CD)*EF_j) + sum(RMC_k*W_C_k*3.664)

        :param carbonates: Список словарей сырья. [{'name': str, 'mass': float, 'calcination_degree': float}]
        :param cement_dust: Словарь с данными о цементной пыли. {'mass': float, 'carbonate_fractions': list, 'calcination_degree': float}
        :param non_carbonate_materials: Список словарей некарбонатных материалов. [{'name': str, 'consumption': float}]
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
        if cement_dust and cement_dust.get('mass', 0) > 0:
            m_cd = cement_dust['mass']
            f_cd = cement_dust.get('calcination_degree', 1.0)
            # W_j_CD - доля исходного карбоната j в составе пыли
            for carb_fraction in cement_dust.get('carbonate_fractions', []):
                 carbonate_data = self.data_service.get_carbonate_data_table_6_1(carb_fraction['name'])
                 if not carbonate_data:
                     raise ValueError(f"Данные для карбоната '{carb_fraction['name']}' в пыли не найдены.")
                 ef_co2 = carbonate_data.get('EF_CO2', 0.0)
                 deduction_for_dust += m_cd * carb_fraction['fraction'] * (1 - f_cd) * ef_co2

        # Третье слагаемое: Выбросы от некарбонатного сырья
        emissions_from_non_carbonates = 0.0
        for material in non_carbonate_materials:
            w_c = self._get_carbon_content(material['name'])
            emissions_from_non_carbonates += material['consumption'] * w_c * self.CARBON_TO_CO2_FACTOR

        total_co2_emissions = emissions_from_carbonates - deduction_for_dust + emissions_from_non_carbonates
        return total_co2_emissions

    def calculate_based_on_clinker(self, clinker_production: float, clinker_composition: list, cement_dust: dict, non_carbonate_materials: list) -> float:
        """
        Рассчитывает выбросы CO2 на основе данных о производстве клинкера.
        
        Реализует формулу 6.2 из методических указаний.
        E_CO2 = CP * sum(W_i * EF_i) + M_CD * sum(W_i_CD * EF_i) + sum(RMC_k*W_C_k*3.664)

        :param clinker_production: Масса произведенного клинкера, т.
        :param clinker_composition: Список словарей состава клинкера. [{'oxide_name': 'CaO', 'fraction': float}, {'oxide_name': 'MgO', 'fraction': float}]
        :param cement_dust: Словарь с данными о цементной пыли. {'mass': float, 'oxide_composition': list}
        :param non_carbonate_materials: Список словарей некарбонатных материалов. [{'name': str, 'consumption': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        # Первое слагаемое: Выбросы от клинкера
        emissions_from_clinker = 0.0
        for oxide in clinker_composition:
            oxide_data = self.data_service.get_oxide_data_table_6_2(oxide['oxide_name'])
            if not oxide_data:
                raise ValueError(f"Данные для оксида '{oxide['oxide_name']}' не найдены.")
            ef_co2 = oxide_data.get('EF_CO2', 0.0)
            emissions_from_clinker += clinker_production * oxide['fraction'] * ef_co2

        # Второе слагаемое: Выбросы от пыли, не возвращенной в печь
        emissions_from_dust = 0.0
        if cement_dust and cement_dust.get('mass', 0) > 0:
            m_cd = cement_dust['mass']
            for oxide in cement_dust.get('oxide_composition', []):
                oxide_data = self.data_service.get_oxide_data_table_6_2(oxide['oxide_name'])
                if not oxide_data:
                    raise ValueError(f"Данные для оксида '{oxide['oxide_name']}' в пыли не найдены.")
                ef_co2 = oxide_data.get('EF_CO2', 0.0)
                emissions_from_dust += m_cd * oxide['fraction'] * ef_co2
        
        # Третье слагаемое: Выбросы от некарбонатного сырья
        emissions_from_non_carbonates = 0.0
        for material in non_carbonate_materials:
            w_c = self._get_carbon_content(material['name'])
            emissions_from_non_carbonates += material['consumption'] * w_c * self.CARBON_TO_CO2_FACTOR

        total_co2_emissions = emissions_from_clinker + emissions_from_dust + emissions_from_non_carbonates
        return total_co2_emissions