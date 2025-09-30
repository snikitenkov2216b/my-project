# calculations/category_11.py - Модуль для расчетов по Категории 11.
# Код обновлен для полной реализации всех формул и добавления валидации.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category11Calculator:
    """
    Класс-калькулятор для категории 11: "Производство азотной кислоты,
    капролактама, глиоксаля и глиоксиловой кислоты".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    def calculate_emissions_from_measurements(self, gas_flow_Q: float, n2o_concentration_C: float) -> float:
        """
        Рассчитывает выбросы N2O на основе данных измерений концентрации и расхода газов.
        
        Реализует формулу 11.1 из методических указаний.
        
        :param gas_flow_Q: Расход отходящих газов, м3/год.
        :param n2o_concentration_C: Средняя концентрация N2O в отходящих газах, мг/м3.
        :return: Масса выбросов N2O в тоннах.
        """
        if gas_flow_Q < 0 or n2o_concentration_C < 0:
            raise ValueError("Расход газа и концентрация не могут быть отрицательными.")
        
        # E (т) = Q (м3/год) * C (мг/м3) * 10^-9 (т/мг)
        return gas_flow_Q * n2o_concentration_C * 10**-9

    def calculate_emissions_with_default_factors(self, process_name: str, production_mass: float) -> float:
        """
        Рассчитывает выбросы N2O на основе данных о производстве и коэффициентах выбросов.
        
        Реализует формулу 11.2 из методических указаний.
        
        :param process_name: Наименование производственного процесса из Таблицы 11.1.
        :param production_mass: Масса произведенной продукции, т.
        :return: Масса выбросов N2O в тоннах.
        """
        if production_mass < 0:
            raise ValueError("Масса произведенной продукции не может быть отрицательной.")

        process_data = self.data_service.get_chemical_process_data_table_11_1(process_name)
        if not process_data:
            raise ValueError(f"Данные для процесса '{process_name}' не найдены в таблице 11.1.")
            
        ef_n2o = process_data.get('EF_N2O', 0.0)
        unit = process_data.get('unit', '')

        if 'кг' in unit:
            # E_N2O (т) = P (т) * EF (кг/т) * 10^-3 (т/кг)
            n2o_emissions = production_mass * ef_n2o * 10**-3
        elif 'т' in unit:
            # E_N2O (т) = P (т) * EF (т/т)
            n2o_emissions = production_mass * ef_n2o
        else:
            raise ValueError(f"Неизвестные единицы измерения для коэффициента выбросов: {unit}")

        return n2o_emissions
        
    def calculate_ef_from_measurements(self, avg_gas_flow_Q: float, avg_n2o_concentration_C: float, avg_production_P: float) -> float:
        """
        Рассчитывает коэффициент выбросов N2O на основе данных измерений.
        
        Реализует формулу 11.3 из методических указаний.
        
        :param avg_gas_flow_Q: Средний расход отходящих газов, м3/час.
        :param avg_n2o_concentration_C: Средняя концентрация N2O, мг/м3.
        :param avg_production_P: Среднее производство продукции, т/час.
        :return: Коэффициент выбросов N2O в кг/т.
        """
        if avg_gas_flow_Q < 0 or avg_n2o_concentration_C < 0:
            raise ValueError("Расход газа и концентрация не могут быть отрицательными.")
        if avg_production_P <= 0:
            raise ValueError("Среднее производство продукции должно быть больше нуля.")
            
        # EF (кг/т) = (Q (м3/ч) * C (мг/м3) * 10^-9 (т/мг)) / P (т/ч) * 1000 (кг/т)
        # Упрощается до: (Q * C * 10^-6) / P
        emission_factor = (avg_gas_flow_Q * avg_n2o_concentration_C * 10**-6) / avg_production_P
        return emission_factor