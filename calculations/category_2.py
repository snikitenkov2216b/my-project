# calculations/category_2.py - Модуль для расчетов по Категории 2.
# Инкапсулирует всю бизнес-логику, связанную со сжиганием углеводородных смесей в факелах.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category2Calculator:
    """
    Класс-калькулятор для категории 2: "Сжигание в факелах".
    Предоставляет методы для расчета выбросов CO2 и CH4.
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к таблицам с коэффициентами.
        """
        self.data_service = data_service

    def calculate_emissions(self, gas_type: str, consumption: float, unit: str) -> dict:
        """
        Рассчитывает выбросы CO2 и CH4 от сжигания газа в факельной установке.
        
        Этот метод реализует формулу 2.1 из методических указаний:
        E_i = FC * EF_i
        
        Используются табличные значения коэффициентов выбросов (EF) из Таблицы 2.1.

        :param gas_type: Наименование вида сжигаемого газа.
        :param consumption: Расход газа в указанных единицах.
        :param unit: Единица измерения расхода ('тонна' или 'тыс. м3').
        :return: Словарь с массами выбросов CO2 и CH4 в тоннах.
                 Например: {'co2': 123.45, 'ch4': 0.12}
        """
        # 1. Получение данных по выбранному типу газа из Таблицы 2.1
        gas_data = self.data_service.get_flare_gas_data_table_2_1(gas_type)
        if not gas_data:
            # Возвращаем нулевые значения, если данные не найдены
            return {'co2': 0.0, 'ch4': 0.0}

        # 2. Выбор коэффициентов выбросов в зависимости от единиц измерения
        if unit == 'тонна':
            ef_co2 = gas_data.get('EF_CO2_t', 0)
            ef_ch4 = gas_data.get('EF_CH4_t', 0)
        elif unit == 'тыс. м3':
            ef_co2 = gas_data.get('EF_CO2_m3', 0)
            ef_ch4 = gas_data.get('EF_CH4_m3', 0)
        else:
            # Если передана некорректная единица измерения
            return {'co2': 0.0, 'ch4': 0.0}

        # 3. Расчет выбросов для CO2 и CH4 по формуле 2.1
        co2_emissions = consumption * ef_co2
        ch4_emissions = consumption * ef_ch4

        # 4. Возврат результатов в виде словаря
        return {'co2': co2_emissions, 'ch4': ch4_emissions}