# calculations/category_9.py - Модуль для расчетов по Категории 9.
# Код обновлен для полной реализации формулы 9.1 и добавления валидации.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category9Calculator:
    """
    Класс-калькулятор для категории 9: "Производство керамических изделий".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    def calculate_emissions(self, raw_materials: list) -> float:
        """
        Рассчитывает выбросы CO2 на основе данных о расходе минерального сырья.
        
        Реализует формулу 9.1 из методических указаний:
        E_CO2 = sum(M_j * MF_j * EF_CO2_j * F_j)
        
        Степень кальцинирования (F_j) принимается равной 1.0 (100%) в соответствии
        с рекомендациями методики при отсутствии фактических данных.

        :param raw_materials: Список словарей, где каждый словарь содержит:
                              {'carbonate_name': str, 'material_mass': float, 
                               'carbonate_fraction': float, 'calcination_degree': float}
        :return: Масса выбросов CO2 в тоннах.
        """
        total_co2_emissions = 0.0
        
        for material in raw_materials:
            carbonate_name = material['carbonate_name']
            material_mass = material['material_mass']
            carbonate_fraction = material['carbonate_fraction']
            calcination_degree = material.get('calcination_degree', 1.0)

            if material_mass < 0 or not (0 <= carbonate_fraction <= 1) or not (0 <= calcination_degree <= 1):
                raise ValueError(f"Для '{carbonate_name}' указаны некорректные значения. Масса должна быть неотрицательной, а доли - в диапазоне от 0 до 1.")

            # Коэффициенты выбросов для карбонатов берутся из Таблицы 6.1
            carbonate_data = self.data_service.get_carbonate_data_table_6_1(carbonate_name)
            if not carbonate_data:
                raise ValueError(f"Данные для карбоната '{carbonate_name}' не найдены в таблице 6.1.")
            
            ef_co2 = carbonate_data.get('EF_CO2', 0.0)
            
            # Расчет выбросов для данного вида сырья
            emission = material_mass * carbonate_fraction * ef_co2 * calcination_degree
            total_co2_emissions += emission
            
        return total_co2_emissions