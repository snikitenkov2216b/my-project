# calculations/category_19.py - Модуль для расчетов по Категории 19.
# Код обновлен с добавлением валидации входных данных.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category19Calculator:
    """
    Класс-калькулятор для категории 19: "Дорожное хозяйство".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    def calculate_from_energy_consumption(self, fuel_consumptions: list) -> float:
        """
        Рассчитывает выбросы CO2 на основе данных о расходе энергоресурсов.
        Реализует формулу 19.1.

        :param fuel_consumptions: Список словарей расхода топлива. 
                                  [{'name': str, 'consumption': float}]
        :return: Масса выбросов CO2 в тоннах.
        """
        total_co2_emissions = 0.0
        for fuel in fuel_consumptions:
            fuel_name = fuel['name']
            consumption = fuel['consumption']
            
            if consumption < 0:
                raise ValueError(f"Расход для '{fuel_name}' не может быть отрицательным.")

            # Используем данные из общей таблицы 18.1 для транспортных топлив
            fuel_data = self.data_service.get_transport_fuel_data_table_18_1(fuel_name)
            if not fuel_data or 'EF_CO2_t' not in fuel_data or fuel_data['EF_CO2_t'] is None:
                # Если в 18.1 нет, пробуем 1.1 (например, для угля)
                fuel_data_1_1 = self.data_service.get_fuel_data_table_1_1(fuel_name)
                if not fuel_data_1_1 or 'EF_CO2_ut' not in fuel_data_1_1:
                    raise ValueError(f"Коэффициент выбросов для '{fuel_name}' не найден.")
                ef_co2_t = fuel_data_1_1['EF_CO2_ut']
            else:
                ef_co2_t = fuel_data['EF_CO2_t']
            
            total_co2_emissions += consumption * ef_co2_t
            
        return total_co2_emissions

    def calculate_from_road_length(self, road_works: list) -> float:
        """
        Рассчитывает выбросы CO2 на основе данных о протяженности дорог и видах работ.
        Реализует формулу 19.2.

        :param road_works: Список словарей с данными о дорожных работах.
                           [{'type': str, 'category': str, 'stage': str, 'length': float, 'years': int}]
        :return: Масса выбросов CO2 в тоннах за год.
        """
        total_co2_emissions_per_year = 0.0
        for work in road_works:
            road_type = work['type']
            road_category = work['category']
            stage = work['stage']
            length = work['length']
            years = work['years']

            if length < 0 or years <= 0:
                raise ValueError("Протяженность дороги должна быть неотрицательной, а срок работ - больше нуля.")

            ef_data = self.data_service.get_road_work_data_table_19_1(road_type, stage, road_category)
            if not ef_data:
                raise ValueError(f"Коэффициент для '{road_type}', '{stage}', категория '{road_category}' не найден.")
            
            ef = ef_data['EF']
            
            # Формула 19.2: E = L * EF
            total_emissions_for_project = length * ef
            
            # Формула 19.3: E_1год = E / Y (распределяем на количество лет)
            emissions_per_year = total_emissions_for_project / years
                
            total_co2_emissions_per_year += emissions_per_year
            
        return total_co2_emissions_per_year