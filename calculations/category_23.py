# calculations/category_23.py - Модуль для расчетов по Категории 23.
# Инкапсулирует бизнес-логику для очистки и сброса сточных вод.
# Код полностью соответствует формулам из Приказа Минприроды РФ от 27.05.2022 N 371.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category23Calculator:
    """
    Класс-калькулятор для категории 23: "Очистка и сброс сточных вод".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    # --- Методы для бытовых сточных вод ---

    def calculate_tow_domestic_by_population(self, population: int, bod_per_capita: float, industrial_factor: float) -> float:
        """
        Рассчитывает общую массу органически разлагаемых веществ в бытовых сточных водах (TOW) 
        на основе численности населения.
        Реализует Уравнение 4.1.

        :param population: Численность населения (P), чел.
        :param bod_per_capita: Образование БПК на одного жителя (BOD), г/чел/сутки.
        :param industrial_factor: Поправочный коэффициент для промышленных сбросов (I), доля.
        :return: Общая масса органических веществ (TOW) в кг БПК/год.
        """
        # TOW (кг БПК/год) = P * BOD (г/чел/сут) * 0.001 (кг/г) * 365 (сут/год) * I
        return population * bod_per_capita * 0.001 * 365 * industrial_factor

    def calculate_emission_factor(self, max_ch4_producing_capacity: float, methane_correction_factor: float) -> float:
        """
        Рассчитывает коэффициент выбросов CH4 для системы очистки.
        Реализует Уравнение 4.3 (аналогично 4.6).

        :param max_ch4_producing_capacity: Максимальная способность образования CH4 (Bo), кг CH4/кг БПК (или ХПК).
        :param methane_correction_factor: Поправочный коэффициент для метана (MCF), доля.
        :return: Коэффициент выбросов (EF), кг CH4/кг БПК (или ХПК).
        """
        # EF = Bo * MCF
        return max_ch4_producing_capacity * methane_correction_factor

    def calculate_domestic_ch4_emissions(self, tow: float, sludge_removed: float, recovered_ch4: float, treatment_systems: list) -> float:
        """
        Рассчитывает общее количество выбросов CH4 из бытовых сточных вод.
        Реализует Уравнение 4.

        :param tow: Общая масса органических веществ в сточных водах, кг БПК/год.
        :param sludge_removed: Азот, удаленный с отстоем сточных вод (S), кг БПК/год.
        :param recovered_ch4: Количество рекуперированного метана (R), кг CH4/год.
        :param treatment_systems: Список систем очистки [{'population_fraction': float, 'treatment_fraction': float, 'emission_factor': float}]
        :return: Общие выбросы CH4 в тоннах/год.
        """
        total_emissions_kg = 0
        for system in treatment_systems:
            U_i = system['population_fraction']
            T_ij = system['treatment_fraction']
            EF_j = system['emission_factor']
            
            # Выбросы для одной группы/системы
            emissions_for_system = (U_i * T_ij * EF_j) * (tow - sludge_removed)
            total_emissions_kg += emissions_for_system

        total_emissions_kg -= recovered_ch4
        
        # Перевод из кг в тонны
        return max(0, total_emissions_kg / 1000)

    # --- Методы для промышленных сточных вод ---

    def calculate_tow_industrial(self, production: float, wastewater_per_product: float, cod: float) -> float:
        """
        Рассчитывает органически разлагаемый материал в промышленных сточных водах (TOW).
        Реализует Уравнение 4.5.

        :param production: Общий объем производства (P), т/год.
        :param wastewater_per_product: Объем сточных вод на тонну продукта (W), м3/т.
        :param cod: Содержание разлагаемых компонентов (COD), кг ХПК/м3.
        :return: Общая масса органических веществ (TOW) в кг ХПК/год.
        """
        # TOW (кг ХПК/год) = P (т/год) * W (м3/т) * COD (кг ХПК/м3)
        return production * wastewater_per_product * cod

    def calculate_industrial_ch4_emissions(self, tow: float, sludge_removed: float, emission_factor: float, recovered_ch4: float) -> float:
        """
        Рассчитывает общее количество выбросов CH4 из промышленных сточных вод.
        Реализует Уравнение 4.4.

        :param tow: Общее количество органически разлагаемого материала, кг ХПК/год.
        :param sludge_removed: Количество органического компонента, удаленного как отстой (S), кг ХПК/год.
        :param emission_factor: Коэффициент выбросов для системы очистки (EF), кг CH4/кг ХПК.
        :param recovered_ch4: Количество рекуперированного метана (R), кг CH4/год.
        :return: Выбросы CH4 в тоннах/год.
        """
        # Выбросы (кг CH4/год) = (TOW - S) * EF - R
        emissions_kg = (tow - sludge_removed) * emission_factor - recovered_ch4
        
        # Перевод из кг в тонны
        return max(0, emissions_kg / 1000)