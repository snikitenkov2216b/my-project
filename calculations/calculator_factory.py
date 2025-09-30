# my-project/calculations/calculator_factory.py
# Фабрика для создания экземпляров калькуляторов.
# Комментарии на русском. Поддержка UTF-8.

from data_models import DataService
from calculations.category_0 import Category0Calculator
from calculations.category_1 import Category1Calculator
from calculations.category_2 import Category2Calculator
from calculations.category_3 import Category3Calculator
from calculations.category_4 import Category4Calculator
from calculations.category_5 import Category5Calculator
from calculations.category_6 import Category6Calculator
from calculations.category_7 import Category7Calculator
from calculations.category_8 import Category8Calculator
from calculations.category_9 import Category9Calculator
from calculations.category_10 import Category10Calculator
from calculations.category_11 import Category11Calculator
from calculations.category_12 import Category12Calculator
from calculations.category_13 import Category13Calculator
from calculations.category_14 import Category14Calculator
from calculations.category_15 import Category15Calculator
from calculations.category_16 import Category16Calculator
from calculations.category_17 import Category17Calculator
from calculations.category_18 import Category18Calculator
from calculations.category_19 import Category19Calculator
from calculations.category_20 import Category20Calculator
from calculations.category_21 import Category21Calculator
from calculations.category_22 import Category22Calculator
from calculations.category_23 import Category23Calculator
from calculations.category_24 import Category24Calculator

class CalculatorFactory:
    """
    Фабрика для создания и предоставления экземпляров калькуляторов для всех категорий.
    """
    def __init__(self, data_service: DataService):
        """
        Конструктор фабрики.
        :param data_service: Экземпляр сервиса данных, который будет использоваться всеми калькуляторами.
        """
        self._data_service = data_service
        self._calculators = {}

    def get_calculator(self, category_name: str):
        """
        Возвращает экземпляр калькулятора для указанной категории.
        Создает экземпляр, если он еще не был создан (ленивая инициализация).
        """
        if category_name not in self._calculators:
            calculator_class = self._get_calculator_class(category_name)
            if calculator_class:
                # Category0Calculator не требует data_service
                if category_name == "Category0":
                    self._calculators[category_name] = calculator_class()
                else:
                    self._calculators[category_name] = calculator_class(self._data_service)
            else:
                return None
        return self._calculators[category_name]

    def _get_calculator_class(self, category_name: str):
        """Вспомогательный метод для сопоставления имени категории с классом калькулятора."""
        calculators_map = {
            "Category0": Category0Calculator,
            "Category1": Category1Calculator,
            "Category2": Category2Calculator,
            "Category3": Category3Calculator,
            "Category4": Category4Calculator,
            "Category5": Category5Calculator,
            "Category6": Category6Calculator,
            "Category7": Category7Calculator,
            "Category8": Category8Calculator,
            "Category9": Category9Calculator,
            "Category10": Category10Calculator,
            "Category11": Category11Calculator,
            "Category12": Category12Calculator,
            "Category13": Category13Calculator,
            "Category14": Category14Calculator,
            "Category15": Category15Calculator,
            "Category16": Category16Calculator,
            "Category17": Category17Calculator,
            "Category18": Category18Calculator,
            "Category19": Category19Calculator,
            "Category20": Category20Calculator,
            "Category21": Category21Calculator,
            "Category22": Category22Calculator,
            "Category23": Category23Calculator,
            "Category24": Category24Calculator,
        }
        return calculators_map.get(category_name)