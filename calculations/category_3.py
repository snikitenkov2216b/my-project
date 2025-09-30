# calculations/category_3.py - Модуль для расчетов по Категории 3.
# Код обновлен с добавлением валидации входных данных.
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
        :raises ValueError: Если входные данные некорректны или данные не найдены.
        """
        if volume < 0:
            raise ValueError("Объем отведения смеси не может быть отрицательным.")

        # 1. Получение данных по концентрациям для выбранного типа газа из Таблицы 3.1
        gas_composition_data = self.data_service.get_fugitive_gas_data_table_3_1(gas_type)
        if not gas_composition_data:
            raise ValueError(f"Данные для смеси '{gas_type}' не найдены в таблице 3.1.")

        w_co2 = gas_composition_data.get('W_CO2', 0.0) # % об.
        w_ch4 = gas_composition_data.get('W_CH4', 0.0) # % об.

        # 2. Получение данных по плотности газов из Таблицы 1.2
        # По умолчанию используются стандартные условия (20 °C)
        density_data = self.data_service.get_density_data_table_1_2()
        rho_co2 = density_data.get('rho_CO2', 0.0) # кг/м3
        rho_ch4 = density_data.get('rho_CH4', 0.0) # кг/м3

        # 3. Расчет выбросов для CO2 и CH4 по формуле 3.1
        # E (т) = FC (тыс. м3) * W (% об.) * rho (кг/м3) * 10^-2
        # Единицы измерения:
        # Плотность в [кг/м3] численно равна плотности в [т/тыс. м3].
        # Множитель 10^-2 переводит проценты [W] в долю.
        # Итого: E [т] = FC [тыс. м3] * (W / 100) * rho [т/тыс. м3]
        
        co2_emissions = volume * w_co2 * rho_co2 * 10**-2
        ch4_emissions = volume * w_ch4 * rho_ch4 * 10**-2

        # 4. Возврат результатов в виде словаря
        return {'co2': co2_emissions, 'ch4': ch4_emissions}