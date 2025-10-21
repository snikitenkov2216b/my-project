# calculations/category_4.py - Модуль для расчетов по Категории 4.
# Код обновлен для использования централизованных констант и валидации данных.
# Комментарии на русском. Поддержка UTF-8.

from data_models_extended import DataService
from config import CARBON_TO_CO2_FACTOR # ИМПОРТ

class Category4Calculator:
    """
    Класс-калькулятор для категории 4: "Нефтепереработка".
    Предоставляет методы для расчета выбросов CO2 от различных
    технологических процессов нефтепереработки.
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к таблицам с коэффициентами.
        """
        self.data_service = data_service
        self.CARBON_TO_CO2_FACTOR = CARBON_TO_CO2_FACTOR

    def calculate_coke_burnoff_continuous(self, Q_y: float, measurements: list) -> float:
        """
        Рассчитывает массу сгоревшего углерода при непрерывной регенерации.
        Реализует формулы 4.1.1, 4.1.2 и 4.1.3.

        :param Q_y: Масса переработанного сырья за период, т.
        :param measurements: Список измерений [{'k_i': float, 'm_i': float}]
        :return: Масса сгоревшего углерода (угл.), т.
        """
        sum_km = sum(m['k_i'] * m['m_i'] for m in measurements[:-1])
        m_n = Q_y - sum(m['m_i'] for m in measurements[:-1])
        k_n = measurements[-1]['k_i']
        
        K_y = (sum_km + (k_n * m_n)) / Q_y # Формула 4.1.2
        
        M_carbon_y = (Q_y * K_y) / 100 # Формула 4.1.1
        return M_carbon_y

    def calculate_coke_burnoff_periodic(self, W_y: float, delta_q: float) -> float:
        """
        Рассчитывает массу сгоревшего углерода при периодической регенерации.
        Реализует формулу 4.1.4.

        :param W_y: Масса регенерируемого катализатора, т.
        :param delta_q: Уменьшение содержания углерода на катализаторе, %.
        :return: Масса сгоревшего углерода (угл.), т.
        """
        M_carbon_y = (W_y * delta_q) / 100
        return M_carbon_y

    def calculate_catalyst_regeneration(self, coke_burnoff: float, coke_carbon_content: float = 0.94) -> float:
        """
        Рассчитывает выбросы CO2 от регенерации катализаторов.
        
        Реализует формулу 4.1 из методических указаний.

        :param coke_burnoff: Масса выгоревшего кокса на катализаторе, т. 
        :param coke_carbon_content: Содержание углерода в коксе, доля (т C/т кокса). По умолчанию 0.94.
        :return: Масса выбросов CO2 в тоннах.
        """
        if coke_burnoff < 0 or not (0 <= coke_carbon_content <= 1):
            raise ValueError("Входные данные должны быть неотрицательными, содержание углерода от 0 до 1.")
            
        co2_emissions = coke_burnoff * coke_carbon_content * self.CARBON_TO_CO2_FACTOR
        return co2_emissions

    def calculate_coke_calcination(self, raw_coke_mass: float, calcined_coke_mass: float, dust_mass: float) -> float:
        """
        Рассчитывает выбросы CO2 от прокалки нефтяного кокса.
        
        Реализует формулу 4.2 из методических указаний.

        :param raw_coke_mass: Количество сырого кокса, поступившего на установку, т.
        :param calcined_coke_mass: Количество полученного прокаленного кокса, т.
        :param dust_mass: Количество уловленной коксовой пыли, т.
        :return: Масса выбросов CO2 в тоннах.
        """
        if raw_coke_mass < 0 or calcined_coke_mass < 0 or dust_mass < 0:
            raise ValueError("Массы не могут быть отрицательными.")

        coke_data = self.data_service.get_fuel_data_table_1_1("Кокс нефтяной и сланцевый")
        if not coke_data:
            raise ValueError("Данные для 'Кокс нефтяной и сланцевый' не найдены в таблице 1.1.")
        
        w_c_coke = coke_data.get('W_C_ut', 0) # т C/т

        carbon_in = raw_coke_mass * w_c_coke
        carbon_out = (calcined_coke_mass + dust_mass) * w_c_coke
        
        co2_emissions = (carbon_in - carbon_out) * self.CARBON_TO_CO2_FACTOR
        
        return max(0, co2_emissions)

    def calculate_hydrogen_production(self, feedstock_name: str, feedstock_consumption: float) -> float:
        """
        Рассчитывает выбросы CO2 от производства водорода.
        
        Реализует формулу 4.3 из методических указаний.

        :param feedstock_name: Наименование углеродсодержащего сырья (топлива).
        :param feedstock_consumption: Расход сырья (топлива), в натуральных единицах (т или тыс. м3).
        :return: Масса выбросов CO2 в тоннах.
        """
        if feedstock_consumption < 0:
            raise ValueError("Расход сырья не может быть отрицательным.")

        feedstock_data = self.data_service.get_fuel_data_table_1_1(feedstock_name)
        if not feedstock_data:
            raise ValueError(f"Данные для сырья '{feedstock_name}' не найдены в таблице 1.1.")
            
        w_c_feedstock = feedstock_data.get('W_C_ut', 0)
        
        co2_emissions = feedstock_consumption * w_c_feedstock * self.CARBON_TO_CO2_FACTOR
        return co2_emissions