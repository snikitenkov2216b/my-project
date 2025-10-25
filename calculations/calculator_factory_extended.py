# calculations/calculator_factory_extended.py
"""
Расширенная фабрика калькуляторов с поддержкой расчетов поглощения ПГ.
Оптимизированная версия с ленивым импортом.
"""
from data_models_extended import DataService, ExtendedDataService


class ExtendedCalculatorFactory:
    """Расширенная фабрика для создания калькуляторов выбросов и поглощения ПГ."""

    # Словари для маппинга классов калькуляторов (ленивая загрузка модулей)
    _EMISSION_CALCULATORS = {
        f"Category{i}": f"calculations.category_{i}" for i in range(25)
    }

    _ABSORPTION_CALCULATORS = {
        "ForestRestoration": ("calculations.absorption_forest_restoration", "ForestRestorationCalculator"),
        "LandReclamation": ("calculations.absorption_forest_restoration", "LandReclamationCalculator"),
        "PermanentForest": ("calculations.absorption_permanent_forest", "PermanentForestCalculator"),
        "ProtectiveForest": ("calculations.absorption_permanent_forest", "ProtectiveForestCalculator"),
        "AgriculturalLand": ("calculations.absorption_agricultural", "AgriculturalLandCalculator"),
        "LandConversion": ("calculations.absorption_agricultural", "LandConversionCalculator"),
    }

    def __init__(self):
        """Инициализация фабрики с обоими типами сервисов данных."""
        self._data_service = None
        self._extended_data_service = None
        self._calculators = {}
        self._absorption_calculators = {}

    @property
    def data_service(self):
        """Ленивая инициализация data_service."""
        if self._data_service is None:
            self._data_service = DataService()
        return self._data_service

    @property
    def extended_data_service(self):
        """Ленивая инициализация extended_data_service."""
        if self._extended_data_service is None:
            self._extended_data_service = ExtendedDataService()
        return self._extended_data_service

    def get_calculator(self, category_name: str):
        """
        Возвращает калькулятор выбросов для указанной категории.
        Использует ленивый импорт для оптимизации.
        """
        if category_name not in self._calculators:
            calculator_class = self._get_emission_calculator_class(category_name)
            if calculator_class:
                if category_name == "Category0":
                    self._calculators[category_name] = calculator_class()
                else:
                    self._calculators[category_name] = calculator_class(self.data_service)
        return self._calculators.get(category_name)

    def get_absorption_calculator(self, calculator_type: str):
        """
        Возвращает калькулятор поглощения ПГ для указанного типа.
        Использует ленивый импорт для оптимизации.
        """
        if calculator_type not in self._absorption_calculators:
            calculator_class = self._get_absorption_calculator_class(calculator_type)
            if calculator_class:
                self._absorption_calculators[calculator_type] = calculator_class()
        return self._absorption_calculators.get(calculator_type)

    def _get_emission_calculator_class(self, category_name: str):
        """Получить класс калькулятора выбросов с ленивым импортом."""
        if category_name not in self._EMISSION_CALCULATORS:
            return None

        module_name = self._EMISSION_CALCULATORS[category_name]
        try:
            module = __import__(module_name, fromlist=[f'{category_name}Calculator'])
            return getattr(module, f'{category_name}Calculator')
        except (ImportError, AttributeError):
            return None

    def _get_absorption_calculator_class(self, calculator_type: str):
        """Получить класс калькулятора поглощения с ленивым импортом."""
        if calculator_type not in self._ABSORPTION_CALCULATORS:
            return None

        module_name, class_name = self._ABSORPTION_CALCULATORS[calculator_type]
        try:
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError):
            return None

    def get_extended_data_service(self) -> ExtendedDataService:
        """Получить расширенный сервис данных для прямого доступа к таблицам."""
        return self.extended_data_service
