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
