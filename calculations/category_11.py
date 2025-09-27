# calculations/category_11.py - Модуль для расчетов по Категории 11.
# Инкапсулирует бизнес-логику для расчета выбросов N2O.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category11Calculator:
    """
    Класс-калькулятор для категории 11: "Производство азотной кислоты,
    капролактама, глиоксаля и глиоксиловой кислоты".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным.
        """
        self.data_service = data_service

    def calculate_n2o_emissions(self, process_name: str, production_mass: float) -> float:
        """
        Рассчитывает выбросы N2O на основе данных о производстве химической продукции.
        
        Реализует формулу 11.2 из методических указаний:
        E_N2O = P * EF_N2O * 10^-3
        
        :param process_name: Наименование производственного процесса из Таблицы 11.1.
        :param production_mass: Масса произведенной продукции, т.
        :return: Масса выбросов N2O в тоннах.
        """
        if production_mass < 0:
            raise ValueError("Масса произведенной продукции не может быть отрицательной.")

        # 1. Получение данных по выбранному процессу из Таблицы 11.1
        process_data = self.data_service.get_ammonia_process_data_table_11_1(process_name)
        if not process_data:
            raise ValueError(f"Данные для процесса '{process_name}' не найдены в таблице 11.1.")
            
        # 2. Извлечение коэффициента выбросов и его единиц измерения
        ef_n2o = process_data.get('EF_N2O', 0.0)
        unit = process_data.get('unit', '')

        # 3. Расчет выбросов по формуле 11.2 с учетом единиц измерения
        # Если EF дан в 'кг/тонну', то для получения результата в тоннах нужно разделить на 1000.
        # Если EF дан в 'т/тонну', то дополнительное преобразование не требуется.
        if 'кг' in unit:
            # E_N2O (т) = P (т) * EF (кг/т) * 10^-3 (т/кг)
            n2o_emissions = production_mass * ef_n2o * 10**-3
        elif 'т' in unit:
            # E_N2O (т) = P (т) * EF (т/т)
            n2o_emissions = production_mass * ef_n2o
        else:
            # На случай непредвиденных единиц измерения
            raise ValueError(f"Неизвестные единицы измерения для коэффициента выбросов: {unit}")

        return n2o_emissions