# calculations/category_21.py - Модуль для расчетов по Категории 21.
# Код обновлен с добавлением валидации входных данных.
# Комментарии на русском. Поддержка UTF-8.

from data_models_extended import DataService

class Category21Calculator:
    """
    Класс-калькулятор для категории 21: "Биологическая переработка твердых отходов".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    def calculate_ch4_emissions(self, waste_mass: float, treatment_type: str, recovered_ch4: float) -> float:
        """
        Рассчитывает выбросы CH4 от биологической переработки отходов.
        Реализует формулу 2.

        :param waste_mass: Масса органических отходов, подвергшихся переработке, т.
        :param treatment_type: Тип переработки ('Компостирование' или 'Анаэробное сбраживание').
        :param recovered_ch4: Количество рекуперированного (собранного) метана, т.
        :return: Масса чистых выбросов CH4 в тоннах.
        """
        if waste_mass < 0 or recovered_ch4 < 0:
            raise ValueError("Масса отходов и количество рекуперированного метана не могут быть отрицательными.")

        treatment_data = self.data_service.get_biological_treatment_data_table_21_1(treatment_type)
        if not treatment_data:
            raise ValueError(f"Данные для типа переработки '{treatment_type}' не найдены в таблице 21.1.")

        ef_ch4 = treatment_data.get('EF_CH4_wet', 0.0) # г/кг

        # Валовые выбросы (т) = Масса (т) * EF (г/кг) * 10^-3 (т*кг/т*г)
        gross_ch4_emissions = waste_mass * ef_ch4 * 10**-3
        
        # Чистые выбросы
        net_ch4_emissions = gross_ch4_emissions - recovered_ch4

        return max(0, net_ch4_emissions)

    def calculate_n2o_emissions(self, waste_mass: float, treatment_type: str) -> float:
        """
        Рассчитывает выбросы N2O от биологической переработки отходов.
        Реализует формулу 2.1.

        :param waste_mass: Масса органических отходов, подвергшихся переработке, т.
        :param treatment_type: Тип переработки ('Компостирование' или 'Анаэробное сбраживание').
        :return: Масса выбросов N2O в тоннах.
        """
        if waste_mass < 0:
            raise ValueError("Масса отходов не может быть отрицательной.")
            
        treatment_data = self.data_service.get_biological_treatment_data_table_21_1(treatment_type)
        if not treatment_data:
            raise ValueError(f"Данные для типа переработки '{treatment_type}' не найдены.")

        ef_n2o = treatment_data.get('EF_N2O_wet', 0.0) # г/кг
        
        # Выбросы (т) = Масса (т) * EF (г/кг) * 10^-3 (т*кг/т*г)
        n2o_emissions = waste_mass * ef_n2o * 10**-3
        
        return n2o_emissions