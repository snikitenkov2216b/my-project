# calculations/category_1.py - Модуль для расчетов по Категории 1.
# Инкапсулирует всю бизнес-логику, связанную со стационарным сжиганием топлива.
# Комментарии на русском. Поддержка UTF-8.

# Импортируем DataService для доступа к табличным данным.
# Указываем полный путь от корня проекта для ясности.
from data_models import DataService

class Category1Calculator:
    """
    Класс-калькулятор для категории 1: "Стационарное сжигание топлива".
    Предоставляет методы для выполнения расчетов на основе данных,
    полученных из пользовательского интерфейса.
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к таблицам с коэффициентами.
        """
        self.data_service = data_service

    def calculate_co2_emissions(self, fuel_name: str, fuel_consumption: float, oxidation_factor: float) -> float:
        """
        Рассчитывает выбросы CO2 от сжигания одного вида топлива.
        
        Этот метод реализует основную формулу 1.1 из методических указаний:
        E_CO2 = FC * EF_CO2 * OF
        
        Для унификации расчетов все данные приводятся к энергетическому эквиваленту в ТДж.

        :param fuel_name: Наименование вида топлива, выбранное пользователем.
        :param fuel_consumption: Расход топлива в натуральных единицах (тонны или тыс. м3).
        :param oxidation_factor: Коэффициент окисления топлива (доля, от 0 до 1).
        :return: Масса выбросов CO2 в тоннах.
        """
        # 1. Получение всех данных по выбранному топливу из Таблицы 1.1
        fuel_data = self.data_service.get_fuel_data_table_1_1(fuel_name)
        if not fuel_data:
            return 0.0

        ncv = fuel_data.get('NCV', 0)
        unit = fuel_data.get('unit', '')
        
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        # 2. Корректировка расчета fc_tj с учетом единиц измерения NCV
        fc_tj = 0.0
        if unit == 'тонна':
            # NCV дан в ТДж/тыс.т, поэтому делим расход в тоннах на 1000
            fc_tj = (fuel_consumption / 1000) * ncv
        elif unit == 'тыс. м3':
            # NCV дан в ТДж/тыс.м3, делить не нужно
            fc_tj = fuel_consumption * ncv
        elif unit == 'тонна у.т.':
            # Для "Прочие горючие отходы" NCV дан в ТДж/т.у.т.
            fc_tj = fuel_consumption * ncv
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
            
        # 3. Получение коэффициента выбросов CO2, соответствующего энергетическим единицам (т CO2/ТДж).
        ef_co2_tj = fuel_data.get('EF_CO2_TJ', 0)

        # 4. Расчет выбросов CO2 по формуле 1.1.
        co2_emissions = fc_tj * ef_co2_tj * oxidation_factor
        
        return co2_emissions