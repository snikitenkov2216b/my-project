# calculations/category_5.py - Модуль для расчетов по Категории 5.
# Код обновлен для использования централизованных констант и валидации данных.
# Комментарии на русском. Поддержка UTF-8.

from data_models_extended import DataService
from config import CARBON_TO_CO2_FACTOR # ИМПОРТ

class Category5Calculator:
    """
    Класс-калькулятор для категории 5: "Производство кокса".
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
        Вспомогательный метод для получения содержания углерода (W_C_ut) из Таблицы 1.1.
        
        :param material_name: Наименование материала/топлива.
        :return: Содержание углерода в т C / ед. изм.
        :raises ValueError: Если данные для материала не найдены.
        """
        data = self.data_service.get_fuel_data_table_1_1(material_name)
        
        if not data or 'W_C_ut' not in data:
            raise ValueError(f"Данные о содержании углерода для '{material_name}' не найдены в таблице 1.1.")
        return data['W_C_ut']

    def calculate_emissions(self, raw_materials: list, fuels: list, main_product: dict, by_products: list) -> float:
        """
        Рассчитывает выбросы CO2 от производства кокса на основе углеродного баланса.
        
        Реализует формулу 5.1 из методических указаний.

        :param raw_materials: Список словарей сырья. [{'name': str, 'consumption': float}]
        :param fuels: Список словарей топлива. [{'name': str, 'consumption': float}]
        :param main_product: Словарь основного продукта. {'name': str, 'production': float}
        :param by_products: Список словарей сопутствующих продуктов. [{'name': str, 'production': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        # --- Расчет входящего углерода (Carbon IN) ---
        carbon_in = 0.0
        
        # Углерод из сырья (коксующиеся угли и т.д.)
        for material in raw_materials:
            if material.get('consumption', 0) < 0:
                raise ValueError("Расход сырья не может быть отрицательным.")
            w_c = self._get_carbon_content(material['name'])
            carbon_in += material['consumption'] * w_c
            
        # Углерод из топлива
        for fuel in fuels:
            if fuel.get('consumption', 0) < 0:
                raise ValueError("Расход топлива не может быть отрицательным.")
            w_c = self._get_carbon_content(fuel['name'])
            carbon_in += fuel['consumption'] * w_c

        # --- Расчет выходящего углерода (Carbon OUT) ---
        carbon_out = 0.0
        
        # Углерод в основном продукте (коксе)
        if main_product and main_product.get('production', 0) > 0:
            if main_product['production'] < 0:
                raise ValueError("Производство основного продукта не может быть отрицательным.")
            w_c_main = self._get_carbon_content(main_product['name'])
            carbon_out += main_product['production'] * w_c_main
            
        # Углерод в сопутствующих продуктах (коксовый газ, смола и т.д.)
        for product in by_products:
            if product.get('production', 0) < 0:
                raise ValueError("Выход сопутствующего продукта не может быть отрицательным.")
            w_c_by = self._get_carbon_content(product['name'])
            carbon_out += product['production'] * w_c_by

        # --- Расчет выбросов CO2 ---
        co2_emissions = (carbon_in - carbon_out) * self.CARBON_TO_CO2_FACTOR
        
        return max(0, co2_emissions)