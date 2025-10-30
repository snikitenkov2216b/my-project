# ui/absorption_utils.py
"""
Вспомогательные функции для вкладок поглощения ПГ.
"""
from PyQt6.QtWidgets import QLineEdit, QMessageBox
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import QLocale
import logging
from typing import Union, Tuple, Optional

try:
    from ui.validation_ranges import ValidationType, ValidationRanges
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False


def create_line_edit(
    parent,
    default_text: str = "0.0",
    validator_params: Union[Tuple[float, float, int], ValidationType, None] = None,
    tooltip: str = "",
    validation_type: Optional[ValidationType] = None
):
    """
    Создает QLineEdit с валидатором и подсказкой.

    :param parent: Родительский виджет
    :param default_text: Текст по умолчанию
    :param validator_params: Параметры валидатора (min, max, decimals) или ValidationType
    :param tooltip: Всплывающая подсказка
    :param validation_type: Тип валидации (альтернатива validator_params)
    :return: QLineEdit с настроенным валидатором
    """
    c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
    line_edit = QLineEdit(default_text)

    # Определяем параметры валидации
    final_validator_params = None
    final_tooltip = tooltip

    if validation_type is not None and VALIDATION_AVAILABLE:
        # Используем ValidationType
        final_validator_params = ValidationRanges.get(validation_type)
        if not tooltip:
            final_tooltip = ValidationRanges.get_tooltip(validation_type)
    elif isinstance(validator_params, ValidationType) and VALIDATION_AVAILABLE:
        # validator_params передан как ValidationType
        final_validator_params = ValidationRanges.get(validator_params)
        if not tooltip:
            final_tooltip = ValidationRanges.get_tooltip(validator_params)
    elif isinstance(validator_params, tuple):
        # Классический способ с кортежем
        final_validator_params = validator_params
    elif validator_params is not None:
        # Неизвестный тип, используем как есть
        final_validator_params = validator_params

    # Применяем валидатор
    if final_validator_params:
        validator = QDoubleValidator(*final_validator_params, parent)
        validator.setLocale(c_locale)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        line_edit.setValidator(validator)

    line_edit.setToolTip(final_tooltip)
    return line_edit


def get_float(line_edit, field_name):
    """Извлекает float из QLineEdit, обрабатывая ошибки."""
    text = line_edit.text().replace(',', '.')
    if not text:
        raise ValueError(f"Поле '{field_name}' не может быть пустым.")
    try:
        value = float(text)
        validator = line_edit.validator()
        if validator:
            state, _, _ = validator.validate(text, 0)
            if state != QDoubleValidator.State.Acceptable:
                raise ValueError(f"Некорректное числовое значение в поле '{field_name}'.")
        return value
    except ValueError:
        raise ValueError(f"Некорректное числовое значение '{text}' в поле '{field_name}'.")


def handle_error(parent, e, tab_name, formula_ref=""):
    """Обрабатывает и отображает ошибки расчета."""
    prefix = f"{tab_name} ({formula_ref}):" if formula_ref else f"{tab_name}:"
    result_text_widget = getattr(parent, "result_text", None)

    if isinstance(e, ValueError):
        QMessageBox.warning(parent, f"Ошибка ввода ({formula_ref})", str(e))
        if result_text_widget:
            result_text_widget.setText("Результат: Ошибка ввода.")
        logging.warning(f"{prefix} Input error - {e}")
    else:
        QMessageBox.critical(parent, f"Ошибка расчета ({formula_ref})", f"Произошла ошибка: {e}")
        if result_text_widget:
            result_text_widget.setText("Результат: Ошибка расчета.")
        logging.error(f"{prefix} Calculation error - {e}", exc_info=True)
