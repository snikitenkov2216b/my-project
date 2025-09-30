# calculations/category_24.py - Модуль для расчетов по Категории 24.
# Инкапсулирует бизнес-логику для расчета выбросов N2O из сточных вод.
# Код полностью соответствует формулам из Приказа Минприроды РФ от 27.05.2022 N 371.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService
from config import N2O_N_TO_N2O_FACTOR # ИМПОРТ

class Category24Calculator:
    """
    Класс-калькулятор для категории 24: "Выбросы закиси азота из сточных вод".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service
        self.N2O_N_TO_N2O_FACTOR = N2O_N_TO_N2O_FACTOR

    def calculate_nitrogen_in_effluent(self, population: int, protein_per_capita: float, fnpr: float, fnon_con: float, find_com: float, sludge_nitrogen_removed: float) -> float:
        """
        Рассчитывает общее количество азота в отводе очищенных сточных вод.
        
        Реализует Уравнение 4.8 из методических указаний.

        :param population: Численность населения (P).
        :param protein_per_capita: Годовое потребление протеина на душу населения, кг/чел/год.
        :param fnpr: Доля азота в протеине (F_NPR).
        :param fnon_con: Коэффициент для непотребленного протеина (F_NON-CON).
        :param find_com: Коэффициент для промышленного и коммерческого протеина (F_IND-COM).
        :param sludge_nitrogen_removed: Азот, удаленный с отстоем сточных вод (N_ОТСТОЙ), кг N/год.
        :return: Общее годовое количество азота в отводе сточных вод (N_сток) в кг N/год.
        """
        # N_сток = (P * Протеин * F_NPR * F_NON-CON * F_IND-COM) - N_ОТСТОЙ
        total_nitrogen = (population * protein_per_capita * fnpr * fnon_con * find_com) - sludge_nitrogen_removed
        return max(0, total_nitrogen)

    def calculate_n2o_emissions_from_effluent(self, nitrogen_in_effluent: float, emission_factor: float) -> float:
        """
        Рассчитывает выбросы N2O из отвода сточных вод.
        
        Реализует Уравнение 4.7 из методических указаний.

        :param nitrogen_in_effluent: Азот в отводе сточных вод (N_сток), кг N/год.
        :param emission_factor: Коэффициент выбросов N2O (EF_сток), кг N2O-N/кг N.
        :return: Выбросы N2O в тоннах/год.
        """
        # Выбросы (кг N2O/год) = N_сток (кг N/год) * EF_сток (кг N2O-N/кг N) * (44/28)
        n2o_emissions_kg = nitrogen_in_effluent * emission_factor * self.N2O_N_TO_N2O_FACTOR
        
        # Перевод из кг в тонны
        return n2o_emissions_kg / 1000