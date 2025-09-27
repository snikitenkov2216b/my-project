# calculations/category_6.py - Модуль для расчетов по Категории 6.
# Инкапсулирует бизнес-логику для производства цемента.
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

    def calculate_based_on_raw_materials(self, carbonates: list) -> float:
        """
        Рассчитывает выбросы CO2 на основе данных о расходе карбонатного сырья.
        
        Реализует основную часть формулы 6.1 из методических указаний:
        E_CO2 = sum(M_j * EF_CO2_j * F_j)
        
        Для упрощения, степень кальцинирования (F_j) принимается равной 1.0 (100%),
        как рекомендовано в методике при отсутствии фактических данных.
        Поправки на цементную пыль и другие материалы не учитываются в базовой реализации.

        :param carbonates: Список словарей, где каждый словарь содержит:
                           {'name': str, 'mass': float} для каждого вида карбоната.
        :return: Масса выбросов CO2 в тоннах.
        """
        total_co2_emissions = 0.0
        
        for carbonate in carbonates:
            carbonate_name = carbonate['name']
            carbonate_mass = carbonate['mass']
            
            # Получаем коэффициент выбросов для данного карбоната из Таблицы 6.1
            carbonate_data = self.data_service.get_carbonate_data_table_6_1(carbonate_name)
            if not carbonate_data:
                raise ValueError(f"Данные для карбоната '{carbonate_name}' не найдены.")
            
            ef_co2 = carbonate_data.get('EF_CO2', 0.0)
            
            # Расчет выбросов для данного вида сырья
            total_co2_emissions += carbonate_mass * ef_co2
            
        return total_co2_emissions

    def calculate_based_on_clinker(self, clinker_production: float, cao_fraction: float, mgo_fraction: float) -> float:
        """
        Рассчитывает выбросы CO2 на основе данных о производстве клинкера.
        
        Реализует основную часть формулы 6.2 из методических указаний:
        E_CO2 = CP * (W_CaO * EF_CaO + W_MgO * EF_MgO)
        
        Поправки на цементную пыль и другие материалы не учитываются в базовой реализации.

        :param clinker_production: Масса произведенного клинкера, т.
        :param cao_fraction: Массовая доля CaO в клинкере, доля (0-1).
        :param mgo_fraction: Массовая доля MgO в клинкере, доля (0-1).
        :return: Масса выбросов CO2 в тоннах.
        """
        # Получаем коэффициенты выбросов для оксидов из Таблицы 6.2
        cao_data = self.data_service.get_oxide_data_table_6_2('CaO')
        mgo_data = self.data_service.get_oxide_data_table_6_2('MgO')
        
        if not cao_data or not mgo_data:
            raise ValueError("Данные для оксидов CaO или MgO не найдены в таблице 6.2.")
            
        ef_cao = cao_data.get('EF_CO2', 0.0)
        ef_mgo = mgo_data.get('EF_CO2', 0.0)
        
        # Расчет выбросов на основе состава клинкера
        emissions_from_clinker = clinker_production * (cao_fraction * ef_cao + mgo_fraction * ef_mgo)
        
        return emissions_from_clinker