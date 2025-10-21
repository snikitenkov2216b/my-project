# calculations/category_24.py - Модуль для расчетов по Категории 24.
# Код обновлен для использования централизованных констант и валидации.
# Комментарии на русском. Поддержка UTF-8.

from data_models_extended import DataService
from config import N2O_N_TO_N2O_FACTOR  # ИМПОРТ


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

    def calculate_nitrogen_in_effluent(
        self,
        population: int,
        protein_per_capita: float,
        fnpr: float,
        fnon_con: float,
        find_com: float,
        sludge_nitrogen_removed: float,
    ) -> float:
        """
        Рассчитывает общее количество азота, сбрасываемого со сточными водами.

        Реализует формулу 4.8 из методических указаний.

        :param population: Численность населения.
        :param protein_per_capita: Потребление белка на душу населения, кг/чел/год.
        :param fnpr: Доля азота в белке (кг N/кг белка).
        :param fnon_con: Коэффициент, учитывающий белок в продуктах, не предназначенных для потребления.
        :param find_com: Коэффициент, учитывающий промышленный и коммерческий сброс белка.
        :param sludge_nitrogen_removed: Общее количество азота, удаленное с осадком, кг N/год.
        :return: Общее количество азота в сточных водах (N_сток), кг N/год.
        """
        if any(
            val < 0
            for val in [
                population,
                protein_per_capita,
                fnpr,
                fnon_con,
                find_com,
                sludge_nitrogen_removed,
            ]
        ):
            raise ValueError("Все входные параметры не могут быть отрицательными.")

        # N_сток (кг N/год) = (P * Protein * F_NPR * F_NON-CON * F_IND-COM) - N_отстой
        total_nitrogen = (
            population * protein_per_capita * fnpr * fnon_con * find_com
        ) - sludge_nitrogen_removed

        return max(0, total_nitrogen)

    def calculate_n2o_emissions_from_effluent(
        self, nitrogen_in_effluent: float, emission_factor: float
    ) -> float:
        """
        Рассчитывает выбросы N2O из сточных вод.

        Реализует формулу 4.7 из методических указаний.

        :param nitrogen_in_effluent: Общее количество азота в сточных водах (N_сток), кг N/год.
        :param emission_factor: Коэффициент выбросов (EF_сток), кг N2O-N/кг N.
        :return: Масса выбросов N2O в тоннах в год.
        """
        if nitrogen_in_effluent < 0 or emission_factor < 0:
            raise ValueError(
                "Количество азота и коэффициент выбросов не могут быть отрицательными."
            )

        # E_N2O (кг/год) = N_сток * EF_сток * (44/28)
        n2o_emissions_kg = (
            nitrogen_in_effluent * emission_factor * self.N2O_N_TO_N2O_FACTOR
        )

        # Перевод в тонны
        n2o_emissions_tonnes = n2o_emissions_kg / 1000

        return n2o_emissions_tonnes
