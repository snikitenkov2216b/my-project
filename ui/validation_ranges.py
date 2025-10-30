# ui/validation_ranges.py
"""
Централизованные диапазоны валидации для полей ввода.
Обеспечивает консистентность и предотвращает ввод некорректных значений.
"""
from typing import Tuple, Optional
from enum import Enum


class ValidationType(Enum):
    """Типы валидации с предустановленными диапазонами."""

    # Доли и коэффициенты (0.0 - 1.0)
    FRACTION = (0.0, 1.0, 4)  # Общие доли
    OXIDATION_FACTOR = (0.0, 1.0, 4)  # Коэффициент окисления
    COMBUSTION_FACTOR = (0.0, 1.0, 4)  # Коэффициент сгорания
    CARBON_CONTENT = (0.0, 1.0, 4)  # Доля углерода
    EFFICIENCY = (0.0, 1.0, 4)  # Эффективность

    # Проценты (0 - 100)
    PERCENT = (0.0, 100.0, 4)  # Общие проценты
    PERCENT_STRICT = (0.0, 100.0, 2)  # Проценты с меньшей точностью
    ORGANIC_MATTER = (0.0, 100.0, 4)  # Содержание органического вещества
    MOISTURE = (0.0, 100.0, 2)  # Влажность
    ASH_CONTENT = (0.0, 100.0, 2)  # Зольность

    # Площади (га)
    AREA_SMALL = (0.0, 1e6, 4)  # Малые площади до 1 млн га
    AREA_LARGE = (0.0, 1e12, 4)  # Большие площади
    AREA_POSITIVE = (0.01, 1e12, 4)  # Площадь строго больше нуля

    # Объемы
    VOLUME_SMALL = (0.0, 1e6, 4)  # Малые объемы
    VOLUME_LARGE = (0.0, 1e12, 6)  # Большие объемы (для топлива)
    VOLUME_POSITIVE = (0.01, 1e12, 4)  # Объем строго больше нуля

    # Массы (тонны, кг)
    MASS_SMALL = (0.0, 1e6, 4)  # До миллиона тонн
    MASS_LARGE = (0.0, 1e12, 4)  # Большие массы
    MASS_POSITIVE = (0.01, 1e12, 4)  # Масса строго больше нуля

    # Физические параметры деревьев
    DIAMETER = (0.1, 1000.0, 2)  # Диаметр дерева, см
    HEIGHT = (0.1, 100.0, 2)  # Высота дерева, м
    TREE_AGE = (1, 500, 0)  # Возраст дерева, лет (целое)

    # Физические параметры почвы
    BULK_DENSITY = (0.1, 5.0, 4)  # Объемная масса почвы, г/см³
    SOIL_DEPTH = (1.0, 200.0, 2)  # Глубина отбора проб, см

    # Временные периоды
    PERIOD_YEARS = (1, 100, 1)  # Период в годах
    PERIOD_YEARS_STRICT = (1, 1000, 0)  # Длительные периоды (целое)

    # Коэффициенты выбросов (могут быть большими)
    EMISSION_FACTOR = (0.0, 1e6, 6)  # Коэффициент выброса
    EMISSION_FACTOR_SMALL = (0.0, 1000.0, 6)  # Малые EF

    # Изменения запасов (могут быть отрицательными)
    CARBON_CHANGE = (-1e9, 1e9, 4)  # Изменение запасов углерода
    BIOMASS_CHANGE = (-1e9, 1e9, 4)  # Изменение биомассы

    # Температуры
    TEMPERATURE = (-100.0, 100.0, 2)  # Температура, °C

    # Общие положительные числа
    POSITIVE_SMALL = (0.0, 1e6, 4)  # Малые положительные
    POSITIVE_LARGE = (0.0, 1e12, 4)  # Большие положительные
    POSITIVE_STRICT = (0.01, 1e12, 4)  # Строго больше нуля

    # Универсальные диапазоны
    ANY_POSITIVE = (0.0, 1e12, 6)  # Любое положительное
    ANY_NUMBER = (-1e12, 1e12, 6)  # Любое число


class ValidationRanges:
    """
    Класс для работы с диапазонами валидации.
    Предоставляет удобный доступ к предустановленным диапазонам.
    """

    @staticmethod
    def get(validation_type: ValidationType) -> Tuple[float, float, int]:
        """
        Получить диапазон валидации.

        :param validation_type: Тип валидации
        :return: Кортеж (min, max, decimals)
        """
        return validation_type.value

    @staticmethod
    def get_tooltip(validation_type: ValidationType) -> str:
        """
        Получить подсказку для типа валидации.

        :param validation_type: Тип валидации
        :return: Строка с описанием допустимого диапазона
        """
        min_val, max_val, decimals = validation_type.value

        # Специальные случаи для более читаемых подсказок
        if validation_type in [ValidationType.FRACTION, ValidationType.OXIDATION_FACTOR,
                              ValidationType.COMBUSTION_FACTOR, ValidationType.CARBON_CONTENT,
                              ValidationType.EFFICIENCY]:
            return f"Допустимые значения: от {min_val} до {max_val} (доля)"

        elif validation_type in [ValidationType.PERCENT, ValidationType.PERCENT_STRICT,
                                ValidationType.ORGANIC_MATTER, ValidationType.MOISTURE,
                                ValidationType.ASH_CONTENT]:
            return f"Допустимые значения: от {min_val} до {max_val}%"

        elif validation_type in [ValidationType.CARBON_CHANGE, ValidationType.BIOMASS_CHANGE]:
            return f"Допустимые значения: от {min_val} до {max_val} (может быть отрицательным)"

        elif min_val > 0:
            return f"Допустимые значения: больше {min_val}"

        elif min_val == 0:
            return f"Допустимые значения: от {min_val} и выше"

        else:
            return f"Допустимые значения: от {min_val} до {max_val}"

    @staticmethod
    def get_custom(min_val: float, max_val: float, decimals: int) -> Tuple[float, float, int]:
        """
        Создать пользовательский диапазон валидации.

        :param min_val: Минимальное значение
        :param max_val: Максимальное значение
        :param decimals: Количество десятичных знаков
        :return: Кортеж (min, max, decimals)
        """
        return (min_val, max_val, decimals)

    @staticmethod
    def validate_value(value: float, validation_type: ValidationType) -> Tuple[bool, Optional[str]]:
        """
        Проверить значение на соответствие диапазону.

        :param value: Проверяемое значение
        :param validation_type: Тип валидации
        :return: (is_valid, error_message)
        """
        min_val, max_val, _ = validation_type.value

        if value < min_val:
            return False, f"Значение {value} меньше минимально допустимого {min_val}"

        if value > max_val:
            return False, f"Значение {value} больше максимально допустимого {max_val}"

        return True, None


# Словарь для быстрого доступа к типичным применениям
FIELD_VALIDATION_MAP = {
    # Коэффициенты
    'oxidation_factor': ValidationType.OXIDATION_FACTOR,
    'combustion_factor': ValidationType.COMBUSTION_FACTOR,
    'carbon_content': ValidationType.CARBON_CONTENT,
    'efficiency': ValidationType.EFFICIENCY,

    # Проценты
    'organic_matter': ValidationType.ORGANIC_MATTER,
    'moisture': ValidationType.MOISTURE,
    'ash_content': ValidationType.ASH_CONTENT,

    # Площади и объемы
    'area': ValidationType.AREA_SMALL,
    'volume': ValidationType.VOLUME_SMALL,

    # Физические параметры
    'diameter': ValidationType.DIAMETER,
    'height': ValidationType.HEIGHT,
    'bulk_density': ValidationType.BULK_DENSITY,
    'soil_depth': ValidationType.SOIL_DEPTH,

    # Периоды
    'period': ValidationType.PERIOD_YEARS,

    # Изменения
    'delta_c': ValidationType.CARBON_CHANGE,
    'delta_biomass': ValidationType.BIOMASS_CHANGE,
}


def get_validation_for_field(field_name: str) -> Tuple[float, float, int]:
    """
    Получить диапазон валидации по имени поля.

    :param field_name: Имя поля (например, 'oxidation_factor')
    :return: Кортеж (min, max, decimals) или ANY_POSITIVE если не найдено
    """
    validation_type = FIELD_VALIDATION_MAP.get(field_name, ValidationType.ANY_POSITIVE)
    return validation_type.value


# Примеры использования:
"""
# В UI коде:
from ui.validation_ranges import ValidationType, ValidationRanges

# Способ 1: Использование через create_line_edit с типом
validator_params = ValidationRanges.get(ValidationType.OXIDATION_FACTOR)
self.oxidation_input = create_line_edit(
    self,
    validator_params=validator_params,
    tooltip=ValidationRanges.get_tooltip(ValidationType.OXIDATION_FACTOR)
)

# Способ 2: Прямое использование значений
self.percent_input = create_line_edit(
    self,
    validator_params=ValidationRanges.get(ValidationType.PERCENT),
    tooltip="Введите процентное содержание (0-100%)"
)

# Способ 3: Валидация значения
value = 0.95
is_valid, error = ValidationRanges.validate_value(value, ValidationType.OXIDATION_FACTOR)
if not is_valid:
    QMessageBox.warning(self, "Ошибка валидации", error)
"""
