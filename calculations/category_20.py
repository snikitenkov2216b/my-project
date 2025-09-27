# calculations/category_20.py - Модуль для расчетов по Категории 20.
# Инкапсулирует бизнес-логику для захоронения и переработки твердых отходов.
# Комментарии на русском. Поддержка UTF-8.

import math
from data_models import DataService

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

    def calculate_landfill_ch4_emissions(self, waste_mass: float, doc: float, doc_f: float, mcf: float, f: float, k: int, years: int) -> list:
        """
        Рассчитывает выбросы CH4 от захоронения отходов за несколько лет,
        используя модель затухания первого порядка (ЗПП).
        
        Реализует логику, описанную в разделе 20 методических указаний.

        :param waste_mass: Масса ежегодно захораниваемых отходов, Гг/год.
        :param doc: Доля способного к разложению органического углерода, доля.
        :param doc_f: Доля DOC, способного к разложению, доля.
        :param mcf: Поправочный коэффициент для метана, доля.
        :param f: Доля CH4 в свалочном газе, доля.
        :param k: Постоянная реакции разложения (1/год).
        :param years: Количество лет для расчета.
        :return: Список ежегодных выбросов CH4 в тоннах.
        """
        # Формула 1.7: Масса разложимого DOC
        ddocm_deposited = waste_mass * doc * doc_f * mcf
        
        ddocm_accumulated_prev = 0
        emissions_list = []

        for year in range(years):
            # Формула 1.5: Масса накопленного DDOCm
            ddocm_accumulated = ddocm_deposited + (ddocm_accumulated_prev * math.exp(-k))
            
            # Формула 1.6: Масса разложившегося DDOCm
            ddocm_decomposed = ddocm_accumulated_prev * (1 - math.exp(-k))
            
            # Формула 1.2: Потенциал образования CH4 (в Гг)
            ch4_generated = ddocm_decomposed * f * (16 / 12)
            
            # Упрощение: OX = 0, R = 0. Выбросы = Образование
            # Переводим из Гг в тонны
            emissions_list.append(ch4_generated * 1000)
            
            ddocm_accumulated_prev = ddocm_accumulated
            
        return emissions_list

    def calculate_biological_treatment_emissions(self, waste_mass: float, treatment_type: str) -> dict:
        """
        Рассчитывает выбросы CH4 и N2O от биологической переработки отходов.
        
        Реализует формулы 2 и 2.1 из методических указаний.

        :param waste_mass: Масса органических отходов, подвергшихся переработке, т.
        :param treatment_type: Тип переработки ('Компостирование' или 'Анаэробное сбраживание').
        :return: Словарь с массами выбросов CH4 и N2O в тоннах.
        """
        treatment_data = self.data_service.get_biological_treatment_data_table_21_1(treatment_type)
        if not treatment_data:
            raise ValueError(f"Данные для типа переработки '{treatment_type}' не найдены.")

        ef_ch4 = treatment_data['EF_CH4_wet'] # г/кг
        ef_n2o = treatment_data['EF_N2O_wet'] # г/кг

        # Расчет выбросов (г/кг эквивалентно т/т)
        ch4_emissions = waste_mass * ef_ch4
        n2o_emissions = waste_mass * ef_n2o

        return {'ch4': ch4_emissions, 'n2o': n2o_emissions}