# calculations/category_21.py - Модуль для расчетов по Категории 21.
# Инкапсулирует бизнес-логику для биологической переработки твердых отходов.
# Код полностью соответствует формулам из Приказа Минприроды РФ от 27.05.2022 N 371.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

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

    def calculate_ch4_emissions(self, waste_mass: float, treatment_type: str, recovered_ch4: float = 0.0) -> float:
        """
        Рассчитывает выбросы CH4 от биологической переработки отходов.
        
        Реализует Уравнение 2 из методических указаний.
        Выбросы CH4 = (BW * EF_CH4) - R

        :param waste_mass: Масса органических отходов (BW), подвергшихся переработке, т.
        :param treatment_type: Тип переработки ('Компостирование' или 'Анаэробное сбраживание').
        :param recovered_ch4: Количество рекуперированного метана (R), т CH4. По умолчанию 0.
        :return: Масса выбросов CH4 в тоннах.
        """
        treatment_data = self.data_service.get_biological_treatment_data_table_21_1(treatment_type)
        if not treatment_data:
            raise ValueError(f"Данные для типа переработки '{treatment_type}' не найдены.")

        ef_ch4 = treatment_data.get('EF_CH4_wet', 0.0) # EF в г/кг

        # Выбросы (т) = Масса (т) * EF (г/кг) / 1000 (г/кг в т/т) - Рекуперация (т)
        ch4_emissions = (waste_mass * ef_ch4 / 1000) - recovered_ch4
        
        return max(0, ch4_emissions)

    def calculate_n2o_emissions(self, waste_mass: float, treatment_type: str) -> float:
        """
        Рассчитывает выбросы N2O от биологической переработки отходов.
        
        Реализует Уравнение 2.1 из методических указаний.
        Выбросы N2O = BW * EF_N2O

        :param waste_mass: Масса органических отходов (BW), подвергшихся переработке, т.
        :param treatment_type: Тип переработки ('Компостирование' или 'Анаэробное сбраживание').
        :return: Масса выбросов N2O в тоннах.
        """
        treatment_data = self.data_service.get_biological_treatment_data_table_21_1(treatment_type)
        if not treatment_data:
            raise ValueError(f"Данные для типа переработки '{treatment_type}' не найдены.")

        ef_n2o = treatment_data.get('EF_N2O_wet', 0.0) # EF в г/кг
        
        # Выбросы (т) = Масса (т) * EF (г/кг) / 1000 (г/кг в т/т)
        n2o_emissions = waste_mass * ef_n2o / 1000
        
        return n2o_emissions