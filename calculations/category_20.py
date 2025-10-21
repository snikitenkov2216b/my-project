# calculations/category_20.py - Модуль для расчетов по Категории 20.
# Код обновлен с добавлением валидации входных данных.
# Комментарии на русском. Поддержка UTF-8.

import math
from data_models_extended import DataService

class Category20Calculator:
    """
    Класс-калькулятор для категории 20: "Захоронение и биологическая
    переработка твердых отходов".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    def calculate_doc_for_mixed_waste(self, waste_composition: list) -> float:
        """
        Рассчитывает долю способного к разложению органического углерода (DOC) для ТКО.
        Реализует Уравнение 1.8.

        :param waste_composition: Список словарей состава отходов [{'type': str, 'fraction': float}]
        :return: Доля DOC в многокомпонентных отходах.
        """
        total_doc = 0.0
        for component in waste_composition:
            component_data = self.data_service.table_20_2.get(component['type'], {})
            doc_wet = component_data.get('doc_wet', 0.0)
            total_doc += doc_wet * component['fraction']
        return total_doc

    def calculate_k_from_half_life(self, t_half: float) -> float:
        """
        Рассчитывает постоянную реакции (k) из периода полураспада (t1/2).
        Реализует Уравнение 1.9.

        :param t_half: Время периода полураспада в годах.
        :return: Постоянная реакции k (1/год).
        """
        if t_half <= 0:
            raise ValueError("Период полураспада должен быть больше нуля.")
        return math.log(2) / t_half

    def calculate_landfill_ch4_emissions(self, historical_waste: list, doc: float, doc_f: float, mcf: float, f: float, k: float, R: float = 0, OX: float = 0) -> list:
        """
        Рассчитывает выбросы CH4 от захоронения отходов, используя модель ЗПП.
        Реализует логику уравнений 1, 1.2, 1.5, 1.6, 1.7.

        :param historical_waste: Список ежегодно захораниваемых отходов за прошлые периоды, Гг/год.
        :param doc: Доля способного к разложению органического углерода, доля.
        :param doc_f: Доля DOC, способного к разложению, доля.
        :param mcf: Поправочный коэффициент для метана, доля.
        :param f: Доля CH4 в свалочном газе, доля.
        :param k: Постоянная реакции разложения (1/год).
        :param R: Количество рекуперированного CH4 за год, Гг. По умолчанию 0.
        :param OX: Коэффициент окисления, доля. По умолчанию 0.
        :return: Список ежегодных выбросов CH4 в тоннах.
        """
        ddocm_accumulated_prev = 0
        emissions_list = []

        for waste_mass in historical_waste:
            if waste_mass < 0:
                raise ValueError("Масса отходов не может быть отрицательной.")
            
            # Уравнение 1.7: Масса разложимого DOC, размещаемого за данный год
            ddocm_deposited = waste_mass * doc * doc_f * mcf
            
            # Уравнение 1.6: Масса DDOCm, разложившегося за год
            ddocm_decomposed = ddocm_accumulated_prev * (1 - math.exp(-k))
            
            # Уравнение 1.5: Масса накопленного DDOCm на конец года
            ddocm_accumulated = ddocm_deposited + (ddocm_accumulated_prev * math.exp(-k))
            
            # Уравнение 1.2: Потенциал образования CH4 (в Гг)
            ch4_generated = ddocm_decomposed * f * (16 / 12)
            
            # Уравнение 1: Расчет итоговых выбросов с учетом рекуперации и окисления
            ch4_emitted = (ch4_generated - R) * (1 - OX)
            
            # Переводим из гигаграммов (Гг) в тонны
            emissions_list.append(max(0, ch4_emitted * 1000))
            
            ddocm_accumulated_prev = ddocm_accumulated
            
        return emissions_list

    def calculate_biological_treatment_emissions(self, waste_mass: float, treatment_type: str) -> dict:
        """
        Рассчитывает выбросы CH4 и N2O от биологической переработки отходов.
        Реализует формулы 2 и 2.1 из раздела 21 методических указаний.

        :param waste_mass: Масса органических отходов, подвергшихся переработке, т.
        :param treatment_type: Тип переработки ('Компостирование' или 'Анаэробное сбраживание').
        :return: Словарь с массами выбросов CH4 и N2O в тоннах.
        """
        if waste_mass < 0:
            raise ValueError("Масса отходов не может быть отрицательной.")

        treatment_data = self.data_service.get_biological_treatment_data_table_21_1(treatment_type)
        if not treatment_data:
            raise ValueError(f"Данные для типа переработки '{treatment_type}' не найдены.")

        ef_ch4 = treatment_data.get('EF_CH4_wet', 0.0) # г/кг
        ef_n2o = treatment_data.get('EF_N2O_wet', 0.0) # г/кг

        # Выбросы (т) = Масса (т) * EF (г/кг) / 1000 (г/кг в т/т)
        ch4_emissions = waste_mass * ef_ch4 / 1000
        n2o_emissions = waste_mass * ef_n2o / 1000

        return {'ch4': ch4_emissions, 'n2o': n2o_emissions}