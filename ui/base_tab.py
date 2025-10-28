# ui/base_tab.py
"""
Базовый класс для всех вкладок UI с общим функционалом.
Обновленная версия с расширенными методами для унификации кода.
"""
from PyQt6.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import QLocale


class BaseTab(QWidget):
    """Базовый класс для вкладок с общими методами."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._input_fields = []  # Список всех полей ввода для очистки

    def _create_line_edit(self, validator_params=None, default_text="", tooltip="", placeholder="0.0"):
        """
        Создает QLineEdit с валидатором.

        Args:
            validator_params: Кортеж (min, max, decimals) для валидатора
            default_text: Текст по умолчанию
            tooltip: Всплывающая подсказка
            placeholder: Текст-подсказка в пустом поле
        """
        line_edit = QLineEdit(default_text)
        line_edit.setPlaceholderText(placeholder)

        # Если не переданы параметры валидатора, используем стандартные
        if validator_params is None:
            validator_params = (-1e12, 1e12, 6)

        validator = QDoubleValidator(*validator_params, self)
        validator.setLocale(self.c_locale)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        line_edit.setValidator(validator)

        if tooltip:
            line_edit.setToolTip(tooltip)

        # Добавляем в список для возможности очистки
        self._input_fields.append(line_edit)
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

    def _create_clear_button(self):
        """
        Создает кнопку для очистки всех полей ввода.

        Returns:
            QPushButton: Кнопка очистки
        """
        clear_button = QPushButton("🗑 Очистить все поля")
        clear_button.setToolTip("Очистить все поля ввода на этой вкладке")
        clear_button.clicked.connect(self._clear_all_fields)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        return clear_button

    def _clear_all_fields(self):
        """Очищает все поля ввода на вкладке."""
        for field in self._input_fields:
            if isinstance(field, QLineEdit):
                field.clear()

    def _add_units_to_label(self, base_label: str, units: str) -> str:
        """
        Добавляет единицы измерения к метке поля.

        Args:
            base_label: Базовая метка
            units: Единицы измерения

        Returns:
            str: Метка с единицами измерения
        """
        return f"{base_label} ({units}):"
