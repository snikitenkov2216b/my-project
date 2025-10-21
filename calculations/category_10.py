# calculations/category_10.py - Модуль для расчетов по Категории 10.
# Код обновлен с добавлением валидации входных данных.
# Комментарии на русском. Поддержка UTF-8.

from data_models_extended import DataService

class Category10Calculator:
    """
    Класс-калькулятор для категории 10: "Производство аммиака".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    def calculate_emissions(self, feedstock_name: str, feedstock_consumption: float, recovered_co2: float) -> float:
        """
        Рассчитывает выбросы CO2 от производства аммиака.
        
        Реализует формулу 10.1 из методических указаний.
        
        Коэффициент окисления (OF) принимается равным 1.0 в соответствии с методикой.

        :param feedstock_name: Наименование углеродсодержащего сырья (топлива).
        :param feedstock_consumption: Расход сырья (топлива) в натуральных единицах (т или тыс. м3).
        :param recovered_co2: Масса CO2, уловленного для дальнейшего использования, т.
        :return: Масса чистых выбросов CO2 в тоннах.
        """
        if feedstock_consumption < 0 or recovered_co2 < 0:
            raise ValueError("Расход сырья и масса уловленного CO2 не могут быть отрицательными.")

        # 1. Получение данных по выбранному сырью из Таблицы 1.1
        feedstock_data = self.data_service.get_fuel_data_table_1_1(feedstock_name)
        if not feedstock_data:
            raise ValueError(f"Данные для сырья '{feedstock_name}' не найдены в таблице 1.1.")
        
        # 2. Получение коэффициента выбросов для натуральных единиц (т CO2 / т или т CO2 / тыс. м3)
        ef_co2_ut = feedstock_data.get('EF_CO2_ut', 0.0)
        
        # 3. Коэффициент окисления по умолчанию равен 1.0 (100%) согласно п. 10.7 методики.
        oxidation_factor = 1.0
        
        # 4. Расчет валовых выбросов CO2
        gross_emissions = feedstock_consumption * ef_co2_ut * oxidation_factor
        
        # 5. Расчет чистых выбросов с учетом уловленного CO2
        net_emissions = gross_emissions - recovered_co2
        
        # Выбросы не могут быть отрицательными
        return max(0, net_emissions)