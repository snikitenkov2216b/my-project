# calculations/category_3.py - Модуль для расчетов по Категории 3.
# Инкапсулирует всю бизнес-логику, связанную с фугитивными выбросами.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category3Calculator:
    """
    Класс-калькулятор для категории 3: "Фугитивные выбросы".
    Предоставляет методы для расчета выбросов CO2 и CH4 от технологических операций.
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к таблицам с коэффициентами.
        """
        self.data_service = data_service

    def calculate_emissions(self, gas_type: str, volume: float) -> dict:
        """
        Рассчитывает фугитивные выбросы CO2 и CH4.
        
        Этот метод реализует формулу 3.1 из методических указаний:
        E_i = FC * W_i * rho_i * 10^-2
        
        Используются табличные значения концентраций (W) из Таблицы 3.1
        и плотностей (rho) из Таблицы 1.2.

        :param gas_type: Наименование вида углеводородной смеси.
        :param volume: Объем отведения (стравливания) смеси, тыс. м3.
        :return: Словарь с массами выбросов CO2 и CH4 в тоннах.
                 Например: {'co2': 123.45, 'ch4': 0.12}
        """
        # 1. Получение данных по концентрациям для выбранного типа газа из Таблицы 3.1
        gas_composition_data = self.data_service.get_fugitive_gas_data_table_3_1(gas_type)
        if not gas_composition_data:
            return {'co2': 0.0, 'ch4': 0.0}

        w_co2 = gas_composition_data.get('W_CO2', 0.0) # % об.
        w_ch4 = gas_composition_data.get('W_CH4', 0.0) # % об.

        # 2. Получение данных по плотности газов из Таблицы 1.2
        # По умолчанию используются стандартные условия (20 °C)
        density_data = self.data_service.get_density_data_table_1_2()
        rho_co2 = density_data.get('rho_CO2', 0.0) # кг/м3
        rho_ch4 = density_data.get('rho_CH4', 0.0) # кг/м3

        # 3. Расчет выбросов для CO2 и CH4 по формуле 3.1
        # E (т) = FC (тыс. м3) * W (% об.) * rho (кг/м3) * 10^-2
        # Единицы: [тыс. м3] * [%] * [кг/м3] * [1/%] = [тыс. м3 * кг/м3] = [1000 * кг] = [т]
        # Таким образом, множитель 10^-2 в формуле корректно переводит проценты в доли.
        
        co2_emissions = volume * w_co2 * rho_co2 * 10**-2
        ch4_emissions = volume * w_ch4 * rho_ch4 * 10**-2

        # 4. Возврат результатов в виде словаря
        return {'co2': co2_emissions, 'ch4': ch4_emissions}