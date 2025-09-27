# calculations/category_12.py - Модуль для расчетов по Категории 12.
# Инкапсулирует бизнес-логику для нефтехимического производства.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category12Calculator:
    """
    Класс-калькулятор для категории 12: "Нефтехимическое производство".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service
        self.CARBON_TO_CO2_FACTOR = 3.664

    def _get_carbon_content(self, substance_name: str) -> float:
        """
        Вспомогательный метод для получения содержания углерода (W_C).
        Сначала ищет в профильной таблице 12.1, затем в общей топливной таблице 1.1.
        
        :param substance_name: Наименование вещества/сырья/продукта.
        :return: Содержание углерода в долях (т C / т вещества).
        :raises ValueError: Если данные для вещества не найдены.
        """
        # Сначала ищем в специализированной таблице 12.1
        data = self.data_service.get_petrochemical_substance_data_table_12_1(substance_name)
        if data and 'W_C' in data:
            return data['W_C']
        
        # Если не найдено, ищем в общей топливной таблице 1.1
        data = self.data_service.get_fuel_data_table_1_1(substance_name)
        if data and 'W_C_ut' in data:
            return data['W_C_ut']
            
        raise ValueError(f"Данные о содержании углерода для '{substance_name}' не найдены в таблицах 12.1 или 1.1.")

    def calculate_emissions_by_balance(self, raw_materials: list, primary_products: list, by_products: list) -> float:
        """
        Рассчитывает выбросы CO2 от нефтехимического производства на основе углеродного баланса.
        
        Реализует формулу 12.1 из методических указаний.

        :param raw_materials: Список словарей сырья. [{'name': str, 'consumption': float}]
        :param primary_products: Список словарей основной продукции. [{'name': str, 'production': float}]
        :param by_products: Список словарей сопутствующей продукции. [{'name': str, 'production': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        # --- Расчет входящего углерода (Carbon IN) ---
        carbon_in = 0.0
        for material in raw_materials:
            w_c = self._get_carbon_content(material['name'])
            carbon_in += material['consumption'] * w_c

        # --- Расчет выходящего углерода (Carbon OUT) ---
        carbon_out = 0.0
        
        # Углерод в основной продукции
        for product in primary_products:
            w_c = self._get_carbon_content(product['name'])
            carbon_out += product['production'] * w_c
            
        # Углерод в сопутствующей продукции
        for product in by_products:
            w_c = self._get_carbon_content(product['name'])
            carbon_out += product['production'] * w_c

        # --- Расчет выбросов CO2 ---
        co2_emissions = (carbon_in - carbon_out) * self.CARBON_TO_CO2_FACTOR
        
        # Выбросы не могут быть отрицательными
        return max(0, co2_emissions)