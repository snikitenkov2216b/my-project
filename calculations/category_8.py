# calculations/category_8.py - Модуль для расчетов по Категории 8.
# Инкапсулирует бизнес-логику для производства стекла.
# Код обновлен для полной реализации формулы 8.1 из методики.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category8Calculator:
    """
    Класс-калькулятор для категории 8: "Производство стекла".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    def calculate_emissions(self, carbonates: list) -> float:
        """
        Рассчитывает выбросы CO2 на основе данных о расходе карбонатного сырья.
        
        Реализует формулу 8.1 из методических указаний:
        E_CO2 = sum(M_j * EF_CO2_j * F_j)
        
        Степень кальцинирования (F_j) принимается равной 1.0 (100%) в соответствии
        с рекомендациями методики при отсутствии фактических данных.

        :param carbonates: Список словарей, где каждый словарь содержит:
                           {'name': str, 'mass': float, 'calcination_degree': float} 
                           для каждого вида карбоната.
        :return: Масса выбросов CO2 в тоннах.
        """
        total_co2_emissions = 0.0
        
        for carbonate in carbonates:
            carbonate_name = carbonate['name']
            carbonate_mass = carbonate['mass']
            # Степень кальцинирования F_j, по умолчанию 1.0
            calcination_degree = carbonate.get('calcination_degree', 1.0)

            # Методика указывает на использование таблиц 6.1 и 8.1.
            # Проверяем обе таблицы для нахождения нужного коэффициента.
            ef_data = self.data_service.get_carbonate_data_table_6_1(carbonate_name)
            if not ef_data:
                ef_data = self.data_service.get_glass_carbonate_data_table_8_1(carbonate_name)
            
            if not ef_data:
                raise ValueError(f"Данные для карбоната '{carbonate_name}' не найдены в таблицах 6.1 или 8.1.")
            
            ef_co2 = ef_data.get('EF_CO2', 0.0)
            
            # Расчет выбросов для данного вида сырья
            total_co2_emissions += carbonate_mass * ef_co2 * calcination_degree
            
        return total_co2_emissions