# calculations/category_4.py - Модуль для расчетов по Категории 4.
# Инкапсулирует всю бизнес-логику, связанную с процессами нефтепереработки.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

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
        self.CARBON_TO_CO2_FACTOR = 3.664

    def calculate_catalyst_regeneration(self, coke_burnoff: float, coke_carbon_content: float = 0.94) -> float:
        """
        Рассчитывает выбросы CO2 от регенерации катализаторов.
        
        Реализует формулу 4.1 из методических указаний:
        E_CO2 = M_кокс * W_C_кокс * 3.664

        :param coke_burnoff: Масса выгоревшего кокса на катализаторе, т.
        :param coke_carbon_content: Содержание углерода в коксе, доля (т C/т кокса).
                                    По умолчанию 0.94 согласно методике.
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
        Коэффициенты содержания углерода берутся из Таблицы 1.1 для "Кокс нефтяной и сланцевый".

        :param raw_coke_mass: Количество сырого кокса, поступившего на установку, т.
        :param calcined_coke_mass: Количество полученного прокаленного кокса, т.
        :param dust_mass: Количество уловленной коксовой пыли, т.
        :return: Масса выбросов CO2 в тоннах.
        """
        if raw_coke_mass < 0 or calcined_coke_mass < 0 or dust_mass < 0:
            raise ValueError("Массы не могут быть отрицательными.")

        # Получаем данные по содержанию углерода из DataService
        coke_data = self.data_service.get_fuel_data_table_1_1("Кокс нефтяной и сланцевый")
        if not coke_data:
            raise ValueError("Данные для 'Кокс нефтяной и сланцевый' не найдены в таблице 1.1.")
        
        # В методике не делается различия в содержании углерода для сырого и прокаленного кокса,
        # поэтому используем одно и то же значение из таблицы.
        w_c_coke = coke_data.get('W_C_ut', 0) # т C/т

        carbon_in = raw_coke_mass * w_c_coke
        carbon_out = (calcined_coke_mass + dust_mass) * w_c_coke
        
        co2_emissions = (carbon_in - carbon_out) * self.CARBON_TO_CO2_FACTOR
        
        # Выбросы не могут быть отрицательными
        return max(0, co2_emissions)

    def calculate_hydrogen_production(self, feedstock_name: str, feedstock_consumption: float) -> float:
        """
        Рассчитывает выбросы CO2 от производства водорода.
        
        Реализует формулу 4.3 из методических указаний:
        E_CO2 = RMC_i * W_C_i * 3.664

        :param feedstock_name: Наименование углеродсодержащего сырья (топлива).
        :param feedstock_consumption: Расход сырья (топлива), в натуральных единицах (т или тыс. м3).
        :return: Масса выбросов CO2 в тоннах.
        """
        if feedstock_consumption < 0:
            raise ValueError("Расход сырья не может быть отрицательным.")

        feedstock_data = self.data_service.get_fuel_data_table_1_1(feedstock_name)
        if not feedstock_data:
            raise ValueError(f"Данные для сырья '{feedstock_name}' не найдены в таблице 1.1.")
            
        # W_C_ut - содержание углерода в тоннах C на тонну топлива или на тыс. м3
        w_c_feedstock = feedstock_data.get('W_C_ut', 0)
        
        co2_emissions = feedstock_consumption * w_c_feedstock * self.CARBON_TO_CO2_FACTOR
        return co2_emissions