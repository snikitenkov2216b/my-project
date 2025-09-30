# calculations/category_14.py - Модуль для расчетов по Категории 14.
# Инкапсулирует бизнес-логику для черной металлургии.
# Код обновлен для полной реализации формул 14.1 и 14.2 из методики.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService
from config import CARBON_TO_CO2_FACTOR # ИМПОРТ

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
        self.CARBON_TO_CO2_FACTOR = CARBON_TO_CO2_FACTOR 

    def _get_carbon_content(self, material_name: str) -> float:
        """
        Вспомогательный метод для получения содержания углерода (W_C).
        Сначала ищет в профильной таблице 14.1, затем в общей топливной таблице 1.1.
        
        :param material_name: Наименование материала/топлива.
        :return: Содержание углерода в т C / ед. изм.
        :raises ValueError: Если данные для материала не найдены.
        """
        data = self.data_service.get_metallurgy_material_data_table_14_1(material_name)
        if data and 'W_C' in data:
            return data['W_C']
        
        data = self.data_service.get_fuel_data_table_1_1(material_name)
        if data and 'W_C_ut' in data:
            return data['W_C_ut']
            
        raise ValueError(f"Данные о содержании углерода для '{material_name}' не найдены в таблицах 14.1 или 1.1.")

    def calculate_emissions_by_process(self, raw_materials: list, fuels: list, products: list, by_products: list) -> float:
        """
        Рассчитывает выбросы CO2 для каждого металлургического процесса в отдельности.
        
        Реализует формулу 14.1 из методических указаний.

        :param raw_materials: Список словарей сырья. [{'name': str, 'consumption': float}]
        :param fuels: Список словарей топлива. [{'name': str, 'consumption': float}]
        :param products: Список словарей основной продукции. [{'name': str, 'production': float}]
        :param by_products: Список словарей сопутствующих продуктов. [{'name': str, 'production': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        # Входящий углерод
        carbon_in_raw = sum(m['consumption'] * self._get_carbon_content(m['name']) for m in raw_materials)
        carbon_in_fuels = sum(f['consumption'] * self._get_carbon_content(f['name']) for f in fuels)
        carbon_in = carbon_in_raw + carbon_in_fuels

        # Выходящий углерод
        carbon_out_products = sum(p['production'] * self._get_carbon_content(p['name']) for p in products)
        carbon_out_by_products = sum(b['production'] * self._get_carbon_content(b['name']) for b in by_products)
        carbon_out = carbon_out_products + carbon_out_by_products

        co2_emissions = (carbon_in - carbon_out) * self.CARBON_TO_CO2_FACTOR
        
        return max(0, co2_emissions)

    def calculate_emissions_by_enterprise_balance(self, inputs: list, outputs: list, stock_changes: list) -> float:
        """
        Рассчитывает выбросы CO2 для предприятия в целом на основе сводного углеродного баланса.
        
        Реализует формулу 14.2 из методических указаний.

        :param inputs: Список входящих потоков. [{'name': str, 'mass': float}]
        :param outputs: Список выходящих потоков. [{'name': str, 'mass': float}]
        :param stock_changes: Список изменений в запасах. [{'name': str, 'mass_change': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        # Углерод во входящих потоках
        carbon_in = sum(i['mass'] * self._get_carbon_content(i['name']) for i in inputs)
        
        # Углерод в выходящих потоках
        carbon_out = sum(o['mass'] * self._get_carbon_content(o['name']) for o in outputs)
        
        # Углерод в изменении запасов
        carbon_stock_change = sum(s['mass_change'] * self._get_carbon_content(s['name']) for s in stock_changes)
        
        co2_emissions = (carbon_in - carbon_out - carbon_stock_change) * self.CARBON_TO_CO2_FACTOR
        
        return co2_emissions