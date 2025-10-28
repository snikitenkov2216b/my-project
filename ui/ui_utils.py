# ui/ui_utils.py
"""
Утилиты для UI компонентов - общие функции и хелперы.
"""
from PyQt6.QtWidgets import QLineEdit, QMessageBox
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import QLocale


# Единый locale для всех валидаторов
C_LOCALE = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)


def create_validated_line_edit(
    parent,
    default_text="0",
    min_val=None,
    max_val=None,
    decimals=2,
    tooltip=""
):
    """
    Создает QLineEdit с настроенным валидатором.

    Args:
        parent: Родительский виджет
        default_text: Текст по умолчанию
        min_val: Минимальное значение
        max_val: Максимальное значение
        decimals: Количество знаков после запятой
        tooltip: Всплывающая подсказка

    Returns:
        QLineEdit: Настроенный виджет
    """
    line_edit = QLineEdit(default_text)

    if min_val is not None and max_val is not None:
        validator = QDoubleValidator(min_val, max_val, decimals, parent)
        validator.setLocale(C_LOCALE)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        line_edit.setValidator(validator)

    if tooltip:
        line_edit.setToolTip(tooltip)

    return line_edit


def get_float_value(line_edit, field_name="поле", allow_empty=False):
    """
    Извлекает float из QLineEdit с обработкой ошибок.

    Args:
        line_edit: QLineEdit виджет
        field_name: Имя поля для сообщений об ошибках
        allow_empty: Разрешить пустое значение (вернет 0.0)

    Returns:
        float: Значение из поля

    Raises:
        ValueError: При некорректном значении
    """
    text = line_edit.text().replace(',', '.').strip()

    if not text:
        if allow_empty:
            return 0.0
        raise ValueError(f"Поле '{field_name}' не может быть пустым")

    try:
        return float(text)
    except ValueError:
        raise ValueError(f"Некорректное значение в поле '{field_name}': {text}")


def show_error(parent, message, title="Ошибка"):
    """
    Показывает диалог с сообщением об ошибке.

    Args:
        parent: Родительский виджет
        message: Текст сообщения
        title: Заголовок окна
    """
    QMessageBox.critical(parent, title, message)


def show_info(parent, message, title="Информация"):
    """
    Показывает информационный диалог.

    Args:
        parent: Родительский виджет
        message: Текст сообщения
        title: Заголовок окна
    """
    QMessageBox.information(parent, title, message)


def show_warning(parent, message, title="Предупреждение"):
    """
    Показывает диалог с предупреждением.

    Args:
        parent: Родительский виджет
        message: Текст сообщения
        title: Заголовок окна
    """
    QMessageBox.warning(parent, title, message)


def format_number(value, decimals=3):
    """
    Форматирует число для отображения.

    Args:
        value: Числовое значение
        decimals: Количество знаков после запятой

    Returns:
        str: Отформатированная строка
    """
    if isinstance(value, (int, float)):
        return f"{value:.{decimals}f}"
    return str(value)


def format_scientific(value, decimals=2):
    """
    Форматирует число в научной нотации.

    Args:
        value: Числовое значение
        decimals: Количество знаков после запятой

    Returns:
        str: Отформатированная строка
    """
    if isinstance(value, (int, float)):
        return f"{value:.{decimals}e}"
    return str(value)


def add_units_to_label(base_label: str, units: str) -> str:
    """
    Добавляет единицы измерения к метке поля.

    Args:
        base_label: Базовая метка (например, "Расход топлива")
        units: Единицы измерения (например, "т/год", "м³/час", "кг")

    Returns:
        str: Метка с единицами измерения

    Examples:
        >>> add_units_to_label("Расход топлива", "т/год")
        'Расход топлива (т/год):'
        >>> add_units_to_label("Температура", "°C")
        'Температура (°C):'
    """
    return f"{base_label} ({units}):"


# Словарь стандартных единиц измерения для различных параметров
STANDARD_UNITS = {
    # Масса
    'mass_tonnes': 'т',
    'mass_kg': 'кг',
    'mass_g': 'г',

    # Масса с временным периодом
    'mass_flow_tonnes_year': 'т/год',
    'mass_flow_kg_hour': 'кг/ч',

    # Объем
    'volume_m3': 'м³',
    'volume_thousand_m3': 'тыс. м³',
    'volume_l': 'л',

    # Объем с временным периодом
    'volume_flow_m3_year': 'м³/год',
    'volume_flow_thousand_m3_year': 'тыс. м³/год',

    # Энергия
    'energy_tj': 'ТДж',
    'energy_gj': 'ГДж',
    'energy_mj': 'МДж',
    'energy_tut': 'т у.т.',

    # Коэффициенты
    'emission_factor_co2_per_tonne': 'т CO₂/т',
    'emission_factor_co2_per_m3': 'т CO₂/тыс. м³',
    'emission_factor_ch4_per_tonne': 'кг CH₄/т',
    'emission_factor_n2o_per_tonne': 'кг N₂O/т',

    # Доли и проценты
    'fraction': 'доля (0-1)',
    'percent': '%',

    # Температура
    'temperature_celsius': '°C',
    'temperature_kelvin': 'K',

    # Результаты выбросов
    'emissions_co2': 'т CO₂',
    'emissions_ch4': 'т CH₄',
    'emissions_n2o': 'т N₂O',
    'emissions_co2_eq': 'т CO₂-экв',

    # Единицы для модулей поглощения
    'area_hectares': 'га',
    'area_m2': 'м²',
    'carbon_tonnes': 'т C',
    'carbon_tonnes_per_ha': 'т C/га',
    'carbon_tonnes_per_year': 'т C/год',
    'carbon_tonnes_per_ha_per_year': 'т C/га/год',
    'diameter_cm': 'см',
    'height_m': 'м',
    'depth_cm': 'см',
    'bulk_density': 'г/см³',
    'biomass_kg': 'кг',
    'biomass_tonnes': 'т',
    'biomass_tonnes_per_ha': 'т/га',
    'period_years': 'лет',
    'combustion_factor': 'доля (0-1)',
    'emission_factor_kg_per_ha': 'кг/га/год',
    'emission_factor_tonnes_c_per_ha': 'т C/га/год',
    'organic_percent': '%',
    'yield_centners_per_ha': 'ц/га',
    'erosion_factor': 'т C/га/год',
    'respiration_rate': 'мг CO₂/м²/час',
    'vegetation_days': 'дни',
}


def get_label_with_standard_units(base_label: str, unit_key: str) -> str:
    """
    Создает метку с единицами измерения из стандартного словаря.

    Args:
        base_label: Базовая метка
        unit_key: Ключ единицы измерения из STANDARD_UNITS

    Returns:
        str: Метка с единицами измерения

    Examples:
        >>> get_label_with_standard_units("Расход топлива", "mass_flow_tonnes_year")
        'Расход топлива (т/год):'
        >>> get_label_with_standard_units("Коэффициент выбросов", "emission_factor_co2_per_tonne")
        'Коэффициент выбросов (т CO₂/т):'
    """
    units = STANDARD_UNITS.get(unit_key, "")
    if units:
        return add_units_to_label(base_label, units)
    return f"{base_label}:"
