# calculations/category_18.py - Модуль для расчетов по Категории 18.
# Код обновлен для полной реализации всех формул и добавления валидации.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category18Calculator:
    """
    Класс-калькулятор для категории 18: "Транспорт".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    def _get_fuel_data(self, fuel_name: str) -> dict:
        """
        Вспомогательный метод для получения данных по топливу из Таблицы 18.1.
        """
        data = self.data_service.get_transport_fuel_data_table_18_1(fuel_name)
        if not data:
            raise ValueError(f"Данные для топлива '{fuel_name}' не найдены в таблице 18.1.")
        return data

    def calculate_road_transport_emissions(self, fuel_name: str, consumption: float, is_volume: bool) -> float:
        """
        Рассчитывает выбросы CO2 от автотранспорта.
        Реализует формулы 18.1 и 18.2.

        :param fuel_name: Наименование топлива.
        :param consumption: Расход топлива (в тоннах или литрах).
        :param is_volume: True, если расход указан в литрах, False - в тоннах.
        :return: Масса выбросов CO2 в тоннах.
        """
        if consumption < 0:
            raise ValueError("Расход топлива не может быть отрицательным.")
            
        fuel_data = self._get_fuel_data(fuel_name)
        ef_co2_t = fuel_data.get('EF_CO2_t')
        
        if ef_co2_t is None:
            raise ValueError(f"Для топлива '{fuel_name}' отсутствует коэффициент выбросов (т CO2/т).")

        if is_volume:
            # Формула 18.2
            rho = fuel_data.get('rho')
            if rho is None:
                raise ValueError(f"Для топлива '{fuel_name}' отсутствует значение плотности.")
            consumption_mass = consumption * rho * 10**-3
        else:
            consumption_mass = consumption

        # Формула 18.1
        co2_emissions = consumption_mass * ef_co2_t
        return co2_emissions

    def calculate_railway_transport_emissions(self, fuel_name: str, consumption: float) -> float:
        """
        Рассчитывает выбросы CO2 от железнодорожного транспорта.
        Реализует формулу 18.3.

        :param fuel_name: Наименование топлива.
        :param consumption: Расход топлива в тоннах.
        :return: Масса выбросов CO2 в тоннах.
        """
        if consumption < 0:
            raise ValueError("Расход топлива не может быть отрицательным.")
            
        fuel_data = self._get_fuel_data(fuel_name)
        ef_co2_t = fuel_data.get('EF_CO2_t')
        
        if ef_co2_t is None:
            raise ValueError(f"Для топлива '{fuel_name}' отсутствует коэффициент выбросов (т CO2/т).")
            
        # Формула 18.3 (аналогична 18.1 для расчетов по массе)
        co2_emissions = consumption * ef_co2_t
        return co2_emissions

    def calculate_water_transport_emissions(self, fuel_name: str, consumption: float) -> float:
        """
        Рассчитывает выбросы CO2 от водного транспорта.
        Реализует формулу 18.4 (в упрощенном виде через NCV).

        :param fuel_name: Наименование топлива.
        :param consumption: Расход топлива в тоннах.
        :return: Масса выбросов CO2 в тоннах.
        """
        if consumption < 0:
            raise ValueError("Расход топлива не может быть отрицательным.")

        fuel_data_18_1 = self._get_fuel_data(fuel_name)
        ef_co2_tj = fuel_data_18_1.get('EF_CO2_TJ')
        if ef_co2_tj is None:
            raise ValueError(f"Для топлива '{fuel_name}' отсутствует коэффициент выбросов (кг/ТДж) в таблице 18.1.")
        
        fuel_data_1_1 = self.data_service.get_fuel_data_table_1_1(fuel_name)
        if not fuel_data_1_1 or 'NCV' not in fuel_data_1_1:
             raise ValueError(f"Данные о низшей теплоте сгорания (NCV) для '{fuel_name}' не найдены в таблице 1.1.")
        ncv = fuel_data_1_1['NCV'] # ТДж/т
        
        # E = FC (т) * NCV (ТДж/т) * EF (кг/ТДж) * 10^-3 (т/кг)
        co2_emissions = consumption * ncv * ef_co2_tj * 10**-3
        return co2_emissions
        
    def calculate_air_transport_emissions(self, fuel_name: str, consumption: float) -> float:
        """
        Рассчитывает выбросы CO2 от воздушного транспорта.
        Реализует формулу 18.5.

        :param fuel_name: Наименование топлива.
        :param consumption: Расход топлива в тоннах.
        :return: Масса выбросов CO2 в тоннах.
        """
        if consumption < 0:
            raise ValueError("Расход топлива не может быть отрицательным.")
            
        fuel_data = self._get_fuel_data(fuel_name)
        ef_co2_t = fuel_data.get('EF_CO2_t')
        
        if ef_co2_t is None:
             raise ValueError(f"Для топлива '{fuel_name}' отсутствует коэффициент выбросов (т CO2/т).")
            
        co2_emissions = consumption * ef_co2_t
        return co2_emissions