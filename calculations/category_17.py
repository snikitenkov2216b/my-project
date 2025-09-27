# calculations/category_17.py - Модуль для расчетов по Категории 17.
# Инкапсулирует бизнес-логику для прочих промышленных процессов.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category17Calculator:
    """
    Класс-калькулятор для категории 17: "Прочие промышленные процессы".
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
        Вспомогательный метод для получения содержания углерода (W_C).
        
        :param material_name: Наименование материала/топлива.
        :return: Содержание углерода в т C / ед. изм.
        :raises ValueError: Если данные для материала не найдены.
        """
        data = self.data_service.get_fuel_data_table_1_1(material_name)
        if data and 'W_C_ut' in data:
            return data['W_C_ut']
        raise ValueError(f"Данные о содержании углерода для '{material_name}' не найдены в таблице 1.1.")

    def calculate_from_fuel_use(self, fuels: list, products: list) -> float:
        """
        Рассчитывает выбросы CO2 от неэнергетического использования топлива.
        Реализует формулу 17.1.

        :param fuels: Список словарей топлива. [{'name': str, 'consumption': float}]
        :param products: Список словарей продукции. [{'name': str, 'production': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        carbon_in = sum(f['consumption'] * self._get_carbon_content(f['name']) for f in fuels)
        carbon_out = sum(p['production'] * self._get_carbon_content(p['name']) for p in products)
        
        co2_emissions = (carbon_in - carbon_out) * self.CARBON_TO_CO2_FACTOR
        return max(0, co2_emissions)

    def calculate_from_reductants(self, reductants: list) -> float:
        """
        Рассчитывает выбросы CO2 от использования восстановителей.
        Реализует формулу 17.2.

        :param reductants: Список словарей восстановителей. [{'name': str, 'consumption': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        carbon_in = sum(r['consumption'] * self._get_carbon_content(r['name']) for r in reductants)
        co2_emissions = carbon_in * self.CARBON_TO_CO2_FACTOR
        return co2_emissions

    def calculate_from_carbonates(self, carbonates: list) -> float:
        """
        Рассчитывает выбросы CO2 от использования карбонатных материалов.
        Реализует формулу 17.3.

        :param carbonates: Список словарей карбонатов. [{'name': str, 'mass': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        total_co2_emissions = 0.0
        for carbonate in carbonates:
            carbonate_name = carbonate['name']
            carbonate_mass = carbonate['mass']
            
            ef_data = self.data_service.get_carbonate_data_table_6_1(carbonate_name)
            if not ef_data:
                ef_data = self.data_service.get_glass_carbonate_data_table_8_1(carbonate_name)
            
            if not ef_data:
                raise ValueError(f"Данные для карбоната '{carbonate_name}' не найдены.")
            
            ef_co2 = ef_data.get('EF_CO2', 0.0)
            total_co2_emissions += carbonate_mass * ef_co2
            
        return total_co2_emissions