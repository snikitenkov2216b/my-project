# ui/absorption_base_tab.py
"""
Базовый класс для вкладок расчетов поглощения ПГ.
Устраняет дублирование кода и предоставляет общие методы.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QLabel, QGroupBox, QScrollArea, QMessageBox, QHBoxLayout,
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale
import logging
from typing import Tuple, Optional

from ui.ui_utils import get_label_with_standard_units


class AbsorptionBaseTab(QWidget):
    """
    Базовый класс для всех вкладок поглощения ПГ.

    Предоставляет:
    - Единый стиль интерфейса
    - Методы создания полей с единицами измерения
    - Кнопку "Очистить все поля"
    - Область результатов
    - Обработку ошибок
    """

    def __init__(self, calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._input_fields = []  # Список всех полей ввода для очистки
        self.result_text = None  # Виджет для отображения результатов

    def _create_main_layout(self):
        """Создает основной layout с прокруткой."""
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Область прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(15)  # Увеличенное расстояние между группами

        scroll_area.setWidget(widget)
        main_layout.addWidget(scroll_area)

        return layout

    def _create_line_edit(
        self,
        default: str = "0.0",
        validator_params: Optional[Tuple[float, float, int]] = None,
        tooltip: str = "",
        placeholder: str = "",
    ) -> QLineEdit:
        """
        Создает поле ввода с валидатором.

        :param default: Значение по умолчанию
        :param validator_params: (min, max, decimals) для QDoubleValidator
        :param tooltip: Подсказка при наведении
        :param placeholder: Текст-заполнитель
        :return: QLineEdit
        """
        line_edit = QLineEdit(default)

        if validator_params:
            validator = QDoubleValidator(*validator_params, self)
            validator.setLocale(self.c_locale)
            validator.setNotation(QDoubleValidator.Notation.StandardNotation)
            line_edit.setValidator(validator)

        if tooltip:
            line_edit.setToolTip(tooltip)

        if placeholder:
            line_edit.setPlaceholderText(placeholder)

        # Стилизация
        line_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
            QLineEdit:disabled {
                background-color: #f0f0f0;
                color: #888;
            }
        """)

        self._input_fields.append(line_edit)
        return line_edit

    def _get_float(self, line_edit: QLineEdit, field_name: str) -> float:
        """
        Извлекает float из QLineEdit с обработкой ошибок.

        :param line_edit: Поле ввода
        :param field_name: Название поля для сообщений об ошибках
        :return: float значение
        :raises ValueError: Если значение некорректно
        """
        text = line_edit.text().replace(',', '.')
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")

        try:
            value = float(text)
            validator = line_edit.validator()
            if validator:
                state, _, _ = validator.validate(text, 0)
                if state != QDoubleValidator.State.Acceptable:
                    raise ValueError(
                        f"Некорректное значение в поле '{field_name}'."
                    )
            return value
        except ValueError:
            raise ValueError(
                f"Некорректное числовое значение '{text}' в поле '{field_name}'."
            )

    def _create_group_box(self, title: str) -> Tuple[QGroupBox, QFormLayout]:
        """
        Создает стилизованный QGroupBox с FormLayout.

        :param title: Заголовок группы
        :return: (QGroupBox, QFormLayout)
        """
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 10px;
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
            }
        """)

        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        return group, layout

    def _create_calculate_button(self, text: str) -> QPushButton:
        """
        Создает стилизованную кнопку расчета.

        :param text: Текст кнопки
        :return: QPushButton
        """
        button = QPushButton(text)
        button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def _create_clear_button(self) -> QPushButton:
        """Создает кнопку очистки всех полей."""
        button = QPushButton("🗑 Очистить все поля")
        button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #fb8c00;
            }
            QPushButton:pressed {
                background-color: #e65100;
            }
        """)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(self._clear_all_fields)
        return button

    def _clear_all_fields(self):
        """Очищает все поля ввода."""
        for field in self._input_fields:
            if isinstance(field, QLineEdit):
                # Восстанавливаем значение по умолчанию (обычно "0.0")
                field.setText("0.0")

        # Очищаем результаты
        if self.result_text:
            self.result_text.clear()

        logging.info(f"{self.__class__.__name__}: All fields cleared")

    def _create_result_area(self) -> QLabel:
        """
        Создает область для отображения результатов.

        :return: QLabel для результатов
        """
        result_label = QLabel("Результат появится здесь после расчета")
        result_label.setWordWrap(True)
        result_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #e8f5e9;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                font-size: 11pt;
                color: #2e7d32;
            }
        """)
        result_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        result_label.setMinimumHeight(80)

        self.result_text = result_label
        return result_label

    def _display_result(self, formula_name: str, result: float, unit: str = "т"):
        """
        Отображает результат расчета.

        :param formula_name: Название формулы
        :param result: Числовой результат
        :param unit: Единица измерения
        """
        if self.result_text:
            text = f"<b>{formula_name}</b><br>"
            text += f"<span style='font-size: 14pt; color: #1b5e20;'>"
            text += f"<b>{result:.4f}</b> {unit}"
            text += "</span>"
            self.result_text.setText(text)
            logging.info(f"{formula_name}: {result:.4f} {unit}")

    def _handle_error(self, e: Exception, formula_ref: str = ""):
        """
        Обрабатывает и отображает ошибки расчета.

        :param e: Исключение
        :param formula_ref: Ссылка на формулу
        """
        prefix = f"{self.__class__.__name__}"
        if formula_ref:
            prefix += f" ({formula_ref})"

        if isinstance(e, ValueError):
            QMessageBox.warning(
                self,
                f"Ошибка ввода",
                f"{formula_ref}: {str(e)}"
            )
            if self.result_text:
                self.result_text.setText(
                    f"<span style='color: #d32f2f;'><b>Ошибка ввода:</b> {str(e)}</span>"
                )
            logging.warning(f"{prefix}: Input error - {e}")
        else:
            QMessageBox.critical(
                self,
                f"Ошибка расчета",
                f"{formula_ref}: Произошла ошибка: {str(e)}"
            )
            if self.result_text:
                self.result_text.setText(
                    f"<span style='color: #d32f2f;'><b>Ошибка расчета:</b> {str(e)}</span>"
                )
            logging.error(f"{prefix}: Calculation error - {e}", exc_info=True)

    def _add_label_with_units(
        self,
        layout: QFormLayout,
        base_label: str,
        unit_key: str,
        widget: QWidget
    ):
        """
        Добавляет поле с автоматическим добавлением единиц измерения.

        :param layout: QFormLayout
        :param base_label: Базовая метка
        :param unit_key: Ключ единицы из STANDARD_UNITS
        :param widget: Виджет поля ввода
        """
        label = get_label_with_standard_units(base_label, unit_key)
        layout.addRow(label, widget)

    def _create_buttons_layout(self, *buttons: QPushButton) -> QHBoxLayout:
        """
        Создает горизонтальный layout для кнопок.

        :param buttons: Кнопки для добавления
        :return: QHBoxLayout
        """
        layout = QHBoxLayout()
        layout.setSpacing(10)

        for button in buttons:
            layout.addWidget(button)

        layout.addStretch()
        return layout

    def get_data(self):
        """
        Собирает данные из всех полей вкладки.

        Returns:
            dict: Словарь с данными вкладки
        """
        data = {}
        for i, field in enumerate(self._input_fields):
            if isinstance(field, QLineEdit):
                field_name = getattr(field, 'objectName', lambda: f'field_{i}')()
                if not field_name or field_name.startswith('qt_'):
                    field_name = f'field_{i}'
                data[field_name] = field.text()

        result = None
        if self.result_text and self.result_text.text():
            result = self.result_text.text()

        return {'fields': data, 'result': result}

    def set_data(self, data):
        """
        Загружает данные во все поля вкладки.

        Args:
            data: dict с данными для загрузки
        """
        if not isinstance(data, dict):
            return

        fields_data = data.get('fields', {})
        for i, field in enumerate(self._input_fields):
            if isinstance(field, QLineEdit):
                field_name = getattr(field, 'objectName', lambda: f'field_{i}')()
                if not field_name or field_name.startswith('qt_'):
                    field_name = f'field_{i}'
                if field_name in fields_data:
                    field.setText(str(fields_data[field_name]))

        # Восстанавливаем результат, если есть
        result = data.get('result')
        if result and self.result_text:
            self.result_text.setText(str(result))

    def clear_fields(self):
        """Очищает все поля ввода на вкладке (алиас для _clear_all_fields)."""
        self._clear_all_fields()
