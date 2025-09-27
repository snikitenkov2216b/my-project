# calculations/category_13.py - Модуль для расчетов по Категории 13.
# Инкапсулирует бизнес-логику для расчета выбросов фторсодержащих веществ.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService

class Category13Calculator:
    """
    Класс-калькулятор для категории 13: "Производство фторсодержащих веществ".
    """

    def __init__(self, data_service: DataService):
        """
        Конструктор класса.
        
        :param data_service: Экземпляр сервиса для доступа к табличным данным (в данной
                             категории не используется, но сохраняется для единообразия).
        """
        self.data_service = data_service

    def calculate_emissions(self, production_mass: float, emission_factor: float) -> float:
        """
        Рассчитывает выбросы фторсодержащих веществ (CHF3 или SF6) на основе
        данных о производстве и коэффициенте выбросов.
        
        Реализует формулу 13.2 из методических указаний:
        E = P * EF * 10^-3
        
        :param production_mass: Масса произведенной основной продукции (ГХФУ-22 или SF6), т.
        :param emission_factor: Коэффициент выбросов побочного продукта (CHF3 или SF6), кг/т.
                                Этот коэффициент зависит от технологии и должен быть
                                определен на основе измерений или проектных данных.
        :return: Масса выбросов парникового газа (CHF3 или SF6) в тоннах.
        """
        if production_mass < 0 or emission_factor < 0:
            raise ValueError("Масса продукции и коэффициент выбросов не могут быть отрицательными.")

        # E (т) = P (т) * EF (кг/т) * 10^-3 (т/кг)
        emissions = production_mass * emission_factor * 10**-3
        
        return emissions