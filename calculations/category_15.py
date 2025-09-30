# calculations/category_15.py - Модуль для расчетов по Категории 15.
# Инкапсулирует бизнес-логику для производства ферросплавов.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService
from config import CARBON_TO_CO2_FACTOR # ИМПОРТ

class Category15Calculator:
    """
    Класс-калькулятор для категории 15: "Производство ферросплавов".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service
        self.CARBON_TO_CO2_FACTOR = CARBON_TO_CO2_FACTOR

    def _get_carbon_content(self, material_name: str) -> float:
        """
        Вспомогательный метод для получения содержания углерода (W_C).
        Ищет данные в таблицах 14.1 (материалы) и 1.1 (топливо).
        
        :param material_name: Наименование материала/топлива.
        :return: Содержание углерода в т C / ед. изм.
        :raises ValueError: Если данные для материала не найдены.
        """
        # Сначала ищем в таблице 14.1 для металлургических материалов
        data = self.data_service.get_metallurgy_material_data_table_14_1(material_name)
        if data and 'W_C' in data:
            return data['W_C']
        
        # Если не найдено, ищем в общей топливной таблице 1.1
        data = self.data_service.get_fuel_data_table_1_1(material_name)
        if data and 'W_C_ut' in data:
            return data['W_C_ut']
            
        raise ValueError(f"Данные о содержании углерода для '{material_name}' не найдены.")

    def calculate_emissions(self, raw_materials: list, fuels: list, products: list, by_products: list) -> float:
        """
        Рассчитывает выбросы CO2 от производства ферросплавов на основе углеродного баланса.
        
        Реализует формулу 15.1 из методических указаний.

        :param raw_materials: Список словарей сырья и восстановителей. [{'name': str, 'consumption': float}]
        :param fuels: Список словарей топлива. [{'name': str, 'consumption': float}]
        :param products: Список словарей основной продукции (ферросплавов). [{'name': str, 'production': float}]
        :param by_products: Список словарей сопутствующей продукции и отходов. [{'name': str, 'production': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        # --- Расчет входящего углерода (Carbon IN) ---
        carbon_in = 0.0
        
        # Углерод из сырья, материалов и восстановителей (кокс, электроды и т.д.)
        for material in raw_materials:
            w_c = self._get_carbon_content(material['name'])
            carbon_in += material['consumption'] * w_c
            
        # Углерод из топлива
        for fuel in fuels:
            w_c = self._get_carbon_content(fuel['name'])
            carbon_in += fuel['consumption'] * w_c

        # --- Расчет выходящего углерода (Carbon OUT) ---
        carbon_out = 0.0
        
        # Углерод в основной продукции (ферросплавах)
        for product in products:
            w_c = self._get_carbon_content(product['name'])
            carbon_out += product['production'] * w_c
            
        # Углерод в сопутствующих продуктах и отходах (шлак, пыль и т.д.)
        for product in by_products:
            w_c = self._get_carbon_content(product['name'])
            carbon_out += product['production'] * w_c

        # --- Расчет выбросов CO2 ---
        co2_emissions = (carbon_in - carbon_out) * self.CARBON_TO_CO2_FACTOR
        
        return max(0, co2_emissions)