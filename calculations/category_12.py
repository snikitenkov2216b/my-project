# calculations/category_12.py - Модуль для расчетов по Категории 12.
# Код обновлен для использования централизованных констант и валидации.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService
from config import CARBON_TO_CO2_FACTOR # ИМПОРТ
# Импортируем калькуляторы для других категорий для реализации формулы 12.2
from calculations.category_1 import Category1Calculator
from calculations.category_2 import Category2Calculator
from calculations.category_3 import Category3Calculator

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
        self.CARBON_TO_CO2_FACTOR = CARBON_TO_CO2_FACTOR
        # Инициализируем калькуляторы других категорий для метода 12.2
        self.cat1_calc = Category1Calculator(data_service)
        self.cat2_calc = Category2Calculator(data_service)
        self.cat3_calc = Category3Calculator(data_service)


    def _get_carbon_content(self, substance_name: str) -> float:
        """
        Вспомогательный метод для получения содержания углерода (W_C).
        Сначала ищет в профильной таблице 12.1, затем в общей топливной таблице 1.1.
        
        :param substance_name: Наименование вещества/сырья/продукта.
        :return: Содержание углерода в долях (т C / т вещества).
        :raises ValueError: Если данные для вещества не найдены.
        """
        data = self.data_service.get_petrochemical_substance_data_table_12_1(substance_name)
        if data and 'W_C' in data:
            return data['W_C']
        
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
        # Входящий углерод
        carbon_in = 0
        for m in raw_materials:
            if m['consumption'] < 0:
                raise ValueError("Расход сырья не может быть отрицательным.")
            carbon_in += m['consumption'] * self._get_carbon_content(m['name'])

        # Выходящий углерод
        carbon_out_primary = 0
        for p in primary_products:
            if p['production'] < 0:
                raise ValueError("Производство основной продукции не может быть отрицательным.")
            carbon_out_primary += p['production'] * self._get_carbon_content(p['name'])
            
        carbon_out_by_products = 0
        for b in by_products:
            if b['production'] < 0:
                raise ValueError("Производство сопутствующей продукции не может быть отрицательным.")
            carbon_out_by_products += b['production'] * self._get_carbon_content(b['name'])
            
        carbon_out = carbon_out_primary + carbon_out_by_products

        co2_emissions = (carbon_in - carbon_out) * self.CARBON_TO_CO2_FACTOR
        
        return max(0, co2_emissions)

    def calculate_emissions_by_source_categories(self, stationary_fuels: list, flare_gases: list, fugitive_gases: list) -> float:
        """
        Рассчитывает выбросы CO2 как сумму выбросов от отдельных категорий источников.
        
        Реализует формулу 12.2 из методических указаний.

        :param stationary_fuels: Данные для расчета по Категории 1. [{'fuel_name': str, 'fuel_consumption': float, 'oxidation_factor': float}]
        :param flare_gases: Данные для расчета по Категории 2. [{'gas_type': str, 'consumption': float, 'unit': str}]
        :param fugitive_gases: Данные для расчета по Категории 3. [{'gas_type': str, 'volume': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        # E_стац
        e_co2_stationary = 0
        for fuel in stationary_fuels:
            fuel_data = self.data_service.get_fuel_data_table_1_1(fuel['fuel_name'])
            ef_co2 = fuel_data.get('EF_CO2_ut', 0.0)
            e_co2_stationary += self.cat1_calc.calculate_total_emissions(
                fuel_consumption=fuel['fuel_consumption'],
                emission_factor=ef_co2,
                oxidation_factor=fuel.get('oxidation_factor', 1.0)
            )

        # E_факел
        e_co2_flare = 0
        for gas in flare_gases:
            emissions = self.cat2_calc.calculate_emissions_with_default_factors(**gas)
            e_co2_flare += emissions.get('co2', 0.0)
            
        # E_фугитив
        e_co2_fugitive = 0
        for gas in fugitive_gases:
            emissions = self.cat3_calc.calculate_emissions(**gas)
            e_co2_fugitive += emissions.get('co2', 0.0)

        total_emissions = e_co2_stationary + e_co2_fugitive + e_co2_flare
        return total_emissions