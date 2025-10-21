# calculations/category_23.py - Модуль для расчетов по Категории 23.
# Код обновлен для полной реализации всех формул и добавления валидации.
# Комментарии на русском. Поддержка UTF-8.

from data_models_extended import DataService

class Category23Calculator:
    """
    Класс-калькулятор для категории 23: "Очистка и сброс сточных вод (выбросы CH4)".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    def calculate_tow_domestic_by_population(self, population: int, bod_per_capita: float, industrial_factor: float) -> float:
        """
        Рассчитывает общую массу органических веществ в сточных водах (TOW) для бытовых стоков.
        Реализует формулу 4.2.

        :param population: Численность населения.
        :param bod_per_capita: Образование БПК на одного жителя, г/чел/сутки.
        :param industrial_factor: Поправочный коэффициент для промышленных сбросов (I).
        :return: Общая масса органических веществ (TOW), кг БПК/год.
        """
        if population < 0 or bod_per_capita < 0 or industrial_factor < 0:
            raise ValueError("Численность населения, БПК и промышленный коэффициент не могут быть отрицательными.")
            
        # TOW (кг БПК/год) = P (чел) * БПК (г/чел/сутки) * I * 365 (сутки/год) * 10^-3 (кг/г)
        tow = population * bod_per_capita * industrial_factor * 365 * 10**-3
        return tow

    def calculate_tow_industrial(self, production: float, wastewater_per_product: float, cod: float) -> float:
        """
        Рассчитывает общую массу органически разлагаемого материала (TOW) для промышленных стоков.
        Реализует формулу 4.4.

        :param production: Объем производства, т/год.
        :param wastewater_per_product: Объем сточных вод на единицу продукции, м³/т.
        :param cod: Химическое потребление кислорода, кг ХПК/м³.
        :return: Общая масса органически разлагаемого материала (TOW), кг ХПК/год.
        """
        if production < 0 or wastewater_per_product < 0 or cod < 0:
            raise ValueError("Все входные параметры для расчета TOW не могут быть отрицательными.")
            
        # TOW (кг ХПК/год) = P (т/год) * W (м³/т) * ХПК (кг ХПК/м³)
        tow = production * wastewater_per_product * cod
        return tow

    def calculate_emission_factor(self, bo: float, mcf: float) -> float:
        """
        Рассчитывает удельный коэффициент выбросов (EF).
        Реализует формулу 4.3.

        :param bo: Максимальная способность образования метана (кг CH4/кг БПК или кг CH4/кг ХПК).
        :param mcf: Поправочный коэффициент для метана.
        :return: Удельный коэффициент выбросов (EF).
        """
        if not (0 <= bo <= 1) or not (0 <= mcf <= 1):
            raise ValueError("Коэффициенты Bo и MCF должны быть в диапазоне от 0 до 1.")
        return bo * mcf

    def calculate_domestic_ch4_emissions(self, tow: float, sludge_removed: float, recovered_ch4: float, systems: list) -> float:
        """
        Рассчитывает выбросы CH4 от бытовых сточных вод.
        Реализует формулу 4.1.

        :param tow: Общая масса органических веществ, кг БПК/год.
        :param sludge_removed: Количество БПК, удаленное с отстоем, кг БПК/год.
        :param recovered_ch4: Количество рекуперированного метана, кг CH4/год.
        :param systems: Список систем очистки. [{'population_fraction': float, 'treatment_fraction': float, 'emission_factor': float}]
        :return: Масса выбросов CH4 в тоннах.
        """
        if tow < 0 or sludge_removed < 0 or recovered_ch4 < 0:
            raise ValueError("TOW, удаленный отстой и рекуперированный метан не могут быть отрицательными.")
        if sludge_removed > tow:
            raise ValueError("Количество удаленного БПК не может превышать общее количество БПК (TOW).")

        sum_term = sum(
            (s['population_fraction'] * s['treatment_fraction'] * s['emission_factor'])
            for s in systems
        )

        # E_CH4 (кг/год) = [(TOW - S) * sum(...) ] - R
        total_ch4_emissions_kg = ((tow - sludge_removed) * sum_term) - recovered_ch4
        
        # Перевод в тонны
        return max(0, total_ch4_emissions_kg / 1000)

    def calculate_industrial_ch4_emissions(self, tow: float, sludge_removed: float, emission_factor: float, recovered_ch4: float) -> float:
        """
        Рассчитывает выбросы CH4 от промышленных сточных вод.
        Реализует формулу 4.5.

        :param tow: Общая масса органически разлагаемого материала, кг ХПК/год.
        :param sludge_removed: Количество ХПК, удаленное с отстоем, кг ХПК/год.
        :param emission_factor: Удельный коэффициент выбросов (EF).
        :param recovered_ch4: Количество рекуперированного метана, кг CH4/год.
        :return: Масса выбросов CH4 в тоннах.
        """
        if tow < 0 or sludge_removed < 0 or recovered_ch4 < 0:
            raise ValueError("TOW, удаленный отстой и рекуперированный метан не могут быть отрицательными.")
        if sludge_removed > tow:
            raise ValueError("Количество удаленного ХПК не может превышать общее количество ХПК (TOW).")

        # E_CH4 (кг/год) = (TOW - S) * EF - R
        total_ch4_emissions_kg = (tow - sludge_removed) * emission_factor - recovered_ch4
        
        # Перевод в тонны
        return max(0, total_ch4_emissions_kg / 1000)