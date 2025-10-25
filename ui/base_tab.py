# ui/base_tab.py
"""
Базовый класс для всех вкладок UI с общим функционалом.
"""
from PyQt6.QtWidgets import QWidget, QLineEdit
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import QLocale


class BaseTab(QWidget):
    """Базовый класс для вкладок с общими методами."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

    def _create_line_edit(self, validator_params=None, default_text="0", tooltip=""):
        """
        Создает QLineEdit с валидатором.

        Args:
            validator_params: Кортеж (min, max, decimals) для валидатора
            default_text: Текст по умолчанию
            tooltip: Всплывающая подсказка
        """
        line_edit = QLineEdit(default_text)
        if validator_params:
            validator = QDoubleValidator(*validator_params, self)
            validator.setLocale(self.c_locale)
            validator.setNotation(QDoubleValidator.Notation.StandardNotation)
            line_edit.setValidator(validator)
        if tooltip:
            line_edit.setToolTip(tooltip)
        return line_edit

    def _get_float(self, line_edit, field_name="поле"):
        """
        Извлекает float значение из QLineEdit.

        Args:
            line_edit: QLineEdit виджет
            field_name: Имя поля для сообщения об ошибке

        Returns:
            float: Числовое значение

        Raises:
            ValueError: Если поле пустое или содержит некорректное значение
        """
        text = line_edit.text().replace(',', '.').strip()
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым")
        try:
            return float(text)
        except ValueError:
            raise ValueError(f"Некорректное значение в поле '{field_name}': {text}")

    def _get_int(self, spin_box, field_name="поле"):
        """
        Извлекает int значение из QSpinBox.

        Args:
            spin_box: QSpinBox виджет
            field_name: Имя поля для сообщения об ошибке

        Returns:
            int: Числовое значение
        """
        return spin_box.value()

    def _format_result(self, **kwargs):
        """
        Форматирует результаты расчета в читаемый вид.

        Args:
            **kwargs: Пары ключ-значение для отображения

        Returns:
            str: Отформатированная строка результата
        """
        result = []
        for key, value in kwargs.items():
            if isinstance(value, float):
                result.append(f"{key}: {value:.3f}")
            else:
                result.append(f"{key}: {value}")
        return "\n".join(result)
