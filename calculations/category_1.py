# calculations/category_1.py - Модуль для расчетов по Категории 1.
# Инкапсулирует всю бизнес-логику, связанную со стационарным сжиганием топлива.
# Код исправлен и дополнен для поддержки всех формул (1.1 - 1.10) из методики.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService
from config import CARBON_TO_CO2_FACTOR # ИМПОРТ

class Category1Calculator:
    """
    Класс-калькулятор для категории 1: "Стационарное сжигание топлива".
    Предоставляет методы для выполнения расчетов на основе данных,
    полученных из пользовательского интерфейса, с учетом различных уровней детализации.
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к таблицам с коэффициентами.
        """
        self.data_service = data_service
        self.CARBON_TO_CO2_FACTOR = CARBON_TO_CO2_FACTOR # ИСПОЛЬЗОВАНИЕ

    # --- Методы для пересчета топлива в энергетические единицы ---

    def convert_to_tonnes_equivalent(self, fuel_name: str, consumption_natural_units: float) -> float:
        """
        Переводит расход топлива из натуральных единиц в тонны условного топлива (т у.т.).
        Реализует формулу 1.2а.

        :param fuel_name: Наименование вида топлива из Таблицы 1.1.
        :param consumption_natural_units: Расход топлива в натуральных единицах (т или тыс. м3).
        :return: Расход топлива в тоннах условного топлива (т у.т.).
        """
        fuel_data = self.data_service.get_fuel_data_table_1_1(fuel_name)
        if not fuel_data or 'k_ut' not in fuel_data:
            raise ValueError(f"Коэффициент перевода в т у.т. для '{fuel_name}' не найден.")
        
        k_ut = fuel_data['k_ut']
        return consumption_natural_units * k_ut

    def convert_to_terajoules(self, fuel_name: str, consumption_natural_units: float) -> float:
        """
        Переводит расход топлива из натуральных единиц в Тераджоули (ТДж).
        Реализует формулу 1.2б.

        :param fuel_name: Наименование вида топлива из Таблицы 1.1.
        :param consumption_natural_units: Расход топлива в натуральных единицах (т или тыс. м3).
        :return: Расход топлива в Тераджоулях (ТДж).
        """
        fuel_data = self.data_service.get_fuel_data_table_1_1(fuel_name)
        if not fuel_data or 'NCV' not in fuel_data:
            raise ValueError(f"Значение низшей теплоты сгорания (NCV) для '{fuel_name}' не найдено.")

        ncv = fuel_data['NCV'] # МДж/кг или МДж/м3, что эквивалентно ГДж/т или ГДж/тыс.м3
        
        # FC (ТДж) = FC (т или тыс.м3) * NCV (ГДж / (т или тыс.м3)) * 10^-3 (ТДж/ГДж)
        return consumption_natural_units * ncv * 10**-3

    # --- Методы для расчета коэффициента выбросов (EF) ---

    def calculate_ef_from_gas_composition_volume(self, components: list, rho_co2: float) -> float:
        """
        Рассчитывает EF_CO2 для газообразного топлива по объемной доле компонентов.
        Реализует формулу 1.3.

        :param components: Список словарей [{'volume_fraction': float, 'carbon_atoms': int}]
        :param rho_co2: Плотность CO2 при условиях измерения, кг/м3.
        :return: Коэффициент выбросов (т CO2/тыс. м3).
        """
        ef_sum = sum(
            (comp['volume_fraction'] * comp['carbon_atoms']) 
            for comp in components
        )
        return ef_sum * rho_co2 * 10**-2

    def calculate_ef_from_gas_composition_mass(self, components: list, fuel_density: float) -> float:
        """
        Рассчитывает EF_CO2 для газообразного топлива по массовой доле компонентов.
        Реализует формулу 1.4.

        :param components: Список словарей [{'mass_fraction': float, 'carbon_atoms': int, 'molar_mass': float}]
        :param fuel_density: Плотность газообразного топлива, кг/м3.
        :return: Коэффициент выбросов (т CO2/тыс. м3).
        """
        molar_mass_co2 = 44.011
        ef_sum = sum(
            ((comp['mass_fraction'] * comp['carbon_atoms'] * molar_mass_co2) / comp['molar_mass'])
            for comp in components
        )
        return ef_sum * fuel_density * 10**-2

    def calculate_ef_from_carbon_content(self, carbon_content: float) -> float:
        """
        Рассчитывает EF_CO2 для твердого/жидкого топлива на основе содержания углерода.
        Реализует формулу 1.5.

        :param carbon_content: Содержание углерода в топливе (доля, т C/т).
        :return: Коэффициент выбросов (т CO2/т).
        """
        return carbon_content * self.CARBON_TO_CO2_FACTOR

    # --- Методы для расчета содержания углерода (Wc) ---

    def calculate_carbon_in_coke(self, ash: float, volatiles: float, sulfur: float) -> float:
        """
        Рассчитывает содержание углерода в коксе (сухом).
        Реализует формулу 1.6.

        :param ash: Содержание золы в коксе, %.
        :param volatiles: Содержание летучих в коксе, %.
        :param sulfur: Содержание серы в коксе, %.
        :return: Содержание углерода в коксе (доля, т C/т).
        """
        if not (0 <= ash <= 100 and 0 <= volatiles <= 100 and 0 <= sulfur <= 100):
            raise ValueError("Содержание компонентов должно быть в процентах от 0 до 100.")
        return (100.0 - (ash + volatiles + sulfur)) / 100.0

    def calculate_carbon_from_ef(self, ef_co2: float) -> float:
        """
        Рассчитывает содержание углерода в топливе на основе коэффициента выбросов.
        Реализует формулу 1.7.

        :param ef_co2: Коэффициент выбросов CO2 (т CO2/т или т CO2/тыс. м3).
        :return: Содержание углерода (т C/т или т C/тыс. м3).
        """
        return ef_co2 / self.CARBON_TO_CO2_FACTOR

    def calculate_carbon_in_coking_coal(self, ash: float, volatiles: float) -> float:
        """
        Рассчитывает содержание углерода в коксующихся углях.
        Реализует формулу 1.10.

        :param ash: Содержание золы в коксующихся углях, %.
        :param volatiles: Содержание летучих в коксующихся углях, %.
        :return: Содержание углерода в углях (доля, т C/т).
        """
        if not (0 <= ash <= 100 and 0 <= volatiles <= 100):
            raise ValueError("Содержание компонентов должно быть в процентах от 0 до 100.")
        return (100.0 - ash - 0.47 * volatiles) / 100.0

    # --- Методы для расчета коэффициента окисления (OF) ---

    def calculate_of_from_heat_loss(self, heat_loss_q4: float) -> float:
        """
        Рассчитывает коэффициент окисления на основе потерь тепла.
        Реализует формулу 1.8.

        :param heat_loss_q4: Потери тепла из-за мех. недожога, %.
        :return: Коэффициент окисления (доля).
        """
        if not (0 <= heat_loss_q4 <= 100):
            raise ValueError("Потери тепла должны быть в процентах от 0 до 100.")
        return (100.0 - heat_loss_q4) / 100.0
    
    def calculate_of_from_ash_carbon(self, carbon_in_ash: float, carbon_in_fuel: float) -> float:
        """
        Рассчитывает коэффициент окисления на основе содержания углерода в золе.
        Реализует формулу 1.9.

        :param carbon_in_ash: Содержание углерода в золе и шлаке за период, т.
        :param carbon_in_fuel: Содержание углерода в израсходованном топливе за тот же период, т.
        :return: Коэффициент окисления (доля).
        """
        if carbon_in_fuel <= 0:
            return 1.0
        if carbon_in_ash > carbon_in_fuel:
            raise ValueError("Углерода в золе не может быть больше, чем в топливе.")
        return 1.0 - (carbon_in_ash / carbon_in_fuel)

    # --- Основной метод расчета выбросов ---
    
    def calculate_total_emissions(self, fuel_consumption: float, emission_factor: float, oxidation_factor: float) -> float:
        """
        Рассчитывает итоговые выбросы CO2 от сжигания топлива.
        Реализует формулу 1.1.

        :param fuel_consumption: Расход топлива в натуральных единицах (тонны или тыс. м3).
        :param emission_factor: Коэффициент выбросов (т CO2/т или т CO2/тыс. м3).
        :param oxidation_factor: Коэффициент окисления (доля).
        :return: Масса выбросов CO2 в тоннах.
        """
        if fuel_consumption < 0 or emission_factor < 0 or not (0 <= oxidation_factor <= 1):
            raise ValueError("Расход и коэффициент выбросов должны быть неотрицательными, а коэффициент окисления - от 0 до 1.")
        
        return fuel_consumption * emission_factor * oxidation_factor