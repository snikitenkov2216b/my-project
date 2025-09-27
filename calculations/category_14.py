# calculations/category_14.py - Модуль для расчетов по Категории 14.
# Инкапсулирует бизнес-логику для черной металлургии.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category14Calculator:
    """
    Класс-калькулятор для категории 14: "Черная металлургия".
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
        Сначала ищет в профильной таблице 14.1, затем в общей топливной таблице 1.1.
        
        :param material_name: Наименование материала/топлива.
        :return: Содержание углерода в т C / ед. изм.
        :raises ValueError: Если данные для материала не найдены.
        """
        # Сначала ищем в специализированной таблице 14.1
        data = self.data_service.get_metallurgy_material_data_table_14_1(material_name)
        if data and 'W_C' in data:
            return data['W_C']
        
        # Если не найдено, ищем в общей топливной таблице 1.1
        data = self.data_service.get_fuel_data_table_1_1(material_name)
        if data and 'W_C_ut' in data:
            return data['W_C_ut']
            
        raise ValueError(f"Данные о содержании углерода для '{material_name}' не найдены в таблицах 14.1 или 1.1.")

    def calculate_emissions(self, raw_materials: list, fuels: list, products: list, by_products: list) -> float:
        """
        Рассчитывает выбросы CO2 от металлургического процесса на основе углеродного баланса.
        
        Реализует формулу 14.1 из методических указаний.

        :param raw_materials: Список словарей сырья. [{'name': str, 'consumption': float}]
        :param fuels: Список словарей топлива. [{'name': str, 'consumption': float}]
        :param products: Список словарей основной продукции. [{'name': str, 'production': float}]
        :param by_products: Список словарей сопутствующих продуктов. [{'name': str, 'production': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        # --- Расчет входящего углерода (Carbon IN) ---
        carbon_in = 0.0
        
        # Углерод из сырья, материалов и восстановителей
        for material in raw_materials:
            w_c = self._get_carbon_content(material['name'])
            carbon_in += material['consumption'] * w_c
            
        # Углерод из топлива
        for fuel in fuels:
            w_c = self._get_carbon_content(fuel['name'])
            carbon_in += fuel['consumption'] * w_c

        # --- Расчет выходящего углерода (Carbon OUT) ---
        carbon_out = 0.0
        
        # Углерод в основной продукции
        for product in products:
            w_c = self._get_carbon_content(product['name'])
            carbon_out += product['production'] * w_c
            
        # Углерод в сопутствующих продуктах
        for product in by_products:
            w_c = self._get_carbon_content(product['name'])
            carbon_out += product['production'] * w_c

        # --- Расчет выбросов CO2 ---
        co2_emissions = (carbon_in - carbon_out) * self.CARBON_TO_CO2_FACTOR
        
        return max(0, co2_emissions)