# calculations/category_13.py - Модуль для расчетов по Категории 13.
# Код обновлен для полной реализации всех формул и добавления валидации.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category13Calculator:
    """
    Класс-калькулятор для категории 13: "Производство фторсодержащих веществ".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к данным.
        """
        self.data_service = data_service

    def calculate_emissions_from_measurements(self, gas_flow_Q: float, gas_concentration_C: float) -> float:
        """
        Рассчитывает выбросы на основе данных измерений концентрации и расхода газов.
        
        Реализует формулу 13.1 из методических указаний.
        
        :param gas_flow_Q: Расход отходящих газов, м3/год.
        :param gas_concentration_C: Средняя концентрация парникового газа в отходящих газах, мг/м3.
        :return: Масса выбросов парникового газа (CHF3 или SF6) в тоннах.
        """
        if gas_flow_Q < 0 or gas_concentration_C < 0:
            raise ValueError("Расход газа и концентрация не могут быть отрицательными.")
            
        # E (т) = Q (м3/год) * C (мг/м3) * 10^-9 (т/мг)
        emissions = gas_flow_Q * gas_concentration_C * 10**-9
        return emissions

    def calculate_emissions_with_default_factors(self, production_mass: float, emission_factor: float) -> float:
        """
        Рассчитывает выбросы на основе данных о производстве и коэффициенте выбросов.
        
        Реализует формулу 13.2 из методических указаний.
        
        :param production_mass: Масса произведенной основной продукции (ГХФУ-22 или SF6), т.
        :param emission_factor: Коэффициент выбросов побочного продукта (CHF3 или SF6), кг/т.
        :return: Масса выбросов парникового газа (CHF3 или SF6) в тоннах.
        """
        if production_mass < 0 or emission_factor < 0:
            raise ValueError("Масса продукции и коэффициент выбросов не могут быть отрицательными.")

        # E (т) = P (т) * EF (кг/т) * 10^-3 (т/кг)
        emissions = production_mass * emission_factor * 10**-3
        return emissions

    def calculate_ef_from_measurements(self, avg_gas_flow_Q: float, avg_gas_concentration_C: float, avg_production_P: float) -> float:
        """
        Рассчитывает коэффициент выбросов на основе данных измерений.
        
        Реализует формулу 13.3 из методических указаний.
        
        :param avg_gas_flow_Q: Средний расход отходящих газов, м3/час.
        :param avg_gas_concentration_C: Средняя концентрация парникового газа, мг/м3.
        :param avg_production_P: Среднее производство продукции, т/час.
        :return: Коэффициент выбросов в кг/т.
        """
        if avg_gas_flow_Q < 0 or avg_gas_concentration_C < 0:
            raise ValueError("Расход газа и концентрация не могут быть отрицательными.")
        if avg_production_P <= 0:
            raise ValueError("Среднее производство продукции должно быть больше нуля.")
        
        # EF (кг/т) = (Q (м3/ч) * C (мг/м3) * 10^-9 (т/мг)) / P (т/ч) * 1000 (кг/т)
        # Упрощается до: (Q * C * 10^-6) / P
        emission_factor = (avg_gas_flow_Q * avg_gas_concentration_C * 10**-6) / avg_production_P
        return emission_factor