# ui/tab_data_mixin.py
"""
Миксин для добавления функциональности сохранения/загрузки данных во вкладки.
"""
from PyQt6.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit


class TabDataMixin:
    """
    Миксин, добавляющий методы get_data, set_data и clear_fields к любой вкладке.
    Автоматически находит все поля ввода через обход атрибутов.
    """

    def get_data(self):
        """
        Собирает данные из всех полей вкладки.

        Returns:
            dict: Словарь с данными вкладки
        """
        data = {}

        # Проходим по всем атрибутам объекта
        for attr_name in dir(self):
            # Пропускаем служебные атрибуты
            if attr_name.startswith('_'):
                continue

            # Ищем поля:
            # - с префиксом input_, f<digit>, drain_
            # - с суффиксом _input (для Category1-24)
            is_input_field = (
                attr_name.startswith('input_') or
                attr_name.startswith('f') and len(attr_name) > 1 and attr_name[1].isdigit() or
                attr_name.startswith('drain_') or
                attr_name.endswith('_input')  # ДОБАВИЛИ ПОДДЕРЖКУ СУФФИКСА
            )
            if not is_input_field:
                continue

            try:
                attr = getattr(self, attr_name)

                # Обрабатываем разные типы виджетов
                value = None
                if isinstance(attr, QLineEdit):
                    value = attr.text()
                elif isinstance(attr, (QSpinBox, QDoubleSpinBox)):
                    value = attr.value()
                elif isinstance(attr, QComboBox):
                    value = {
                        'type': 'QComboBox',
                        'current_index': attr.currentIndex(),
                        'current_text': attr.currentText()
                    }
                elif isinstance(attr, QCheckBox):
                    value = attr.isChecked()
                elif isinstance(attr, QTextEdit) and attr_name not in ['result_text', 'result_label']:
                    # Сохраняем QTextEdit, но не result_text
                    value = attr.toPlainText()

                # Фильтрация пустых значений для уменьшения размера файлов
                if value is not None:
                    if isinstance(value, str) and not value.strip():
                        continue  # Пропускаем пустые строки
                    elif isinstance(value, (int, float)) and value == 0:
                        continue  # Пропускаем нулевые числа
                    elif isinstance(value, dict) and value.get('current_index', -1) == 0:
                        continue  # Пропускаем ComboBox с индексом 0 (первый элемент)
                    data[attr_name] = value
            except:
                continue

        # Добавляем результат, если есть
        result = None
        try:
            if hasattr(self, 'result_label') and self.result_label:
                # result_label может быть QLabel или QTextEdit
                if hasattr(self.result_label, 'text'):
                    result = self.result_label.text()
                elif hasattr(self.result_label, 'toPlainText'):
                    result = self.result_label.toPlainText()
            elif hasattr(self, 'result_text') and self.result_text:
                if hasattr(self.result_text, 'text'):
                    result = self.result_text.text()
                elif hasattr(self.result_text, 'toPlainText'):
                    result = self.result_text.toPlainText()
        except:
            result = None

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

        # Проходим по всем атрибутам объекта
        for attr_name, value in fields_data.items():
            if not hasattr(self, attr_name):
                continue

            try:
                attr = getattr(self, attr_name)

                # Устанавливаем значения в зависимости от типа виджета
                if isinstance(attr, QLineEdit):
                    attr.setText(str(value) if value else "")
                elif isinstance(attr, QSpinBox):
                    try:
                        attr.setValue(int(value) if value else 0)
                    except:
                        attr.setValue(0)
                elif isinstance(attr, QDoubleSpinBox):
                    try:
                        attr.setValue(float(value) if value else 0.0)
                    except:
                        attr.setValue(0.0)
                elif isinstance(attr, QComboBox) and isinstance(value, dict):
                    if value.get('type') == 'QComboBox':
                        index = value.get('current_index', 0)
                        if 0 <= index < attr.count():
                            attr.setCurrentIndex(index)
                elif isinstance(attr, QCheckBox):
                    attr.setChecked(bool(value))
                elif isinstance(attr, QTextEdit) and attr_name not in ['result_text', 'result_label']:
                    attr.setPlainText(str(value) if value else "")
            except:
                continue

        # Восстанавливаем результат, если есть
        result = data.get('result')
        if result:
            try:
                if hasattr(self, 'result_label') and self.result_label:
                    if hasattr(self.result_label, 'setText'):
                        self.result_label.setText(str(result))
                    elif hasattr(self.result_label, 'setPlainText'):
                        self.result_label.setPlainText(str(result))
                elif hasattr(self, 'result_text') and self.result_text:
                    if hasattr(self.result_text, 'setText'):
                        self.result_text.setText(str(result))
                    elif hasattr(self.result_text, 'setPlainText'):
                        self.result_text.setPlainText(str(result))
            except:
                pass

    def clear_fields(self):
        """Очищает все поля ввода на вкладке."""
        # Проходим по всем атрибутам объекта
        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue

            # Ищем поля ввода (с префиксом и суффиксом)
            is_input_field = (
                attr_name.startswith('input_') or
                attr_name.startswith('f') and len(attr_name) > 1 and attr_name[1].isdigit() or
                attr_name.startswith('drain_') or
                attr_name.endswith('_input')  # ДОБАВИЛИ ПОДДЕРЖКУ СУФФИКСА
            )
            if not is_input_field:
                continue

            try:
                attr = getattr(self, attr_name)

                # Очищаем в зависимости от типа виджета
                if isinstance(attr, QLineEdit):
                    attr.clear()
                elif isinstance(attr, QSpinBox):
                    attr.setValue(0)
                elif isinstance(attr, QDoubleSpinBox):
                    attr.setValue(0.0)
                elif isinstance(attr, QComboBox):
                    attr.setCurrentIndex(0)
                elif isinstance(attr, QCheckBox):
                    attr.setChecked(False)
                elif isinstance(attr, QTextEdit) and attr_name not in ['result_text', 'result_label']:
                    attr.clear()
            except:
                continue

        # Очищаем результат
        try:
            if hasattr(self, 'result_label') and self.result_label:
                if hasattr(self.result_label, 'setText'):
                    self.result_label.setText("Результат появится здесь после расчета")
                elif hasattr(self.result_label, 'setPlainText'):
                    self.result_label.setPlainText("Результат появится здесь после расчета")
            elif hasattr(self, 'result_text') and self.result_text:
                if hasattr(self.result_text, 'setText'):
                    self.result_text.setText("Результат появится здесь после расчета")
                elif hasattr(self.result_text, 'setPlainText'):
                    self.result_text.setPlainText("Результат появится здесь после расчета")
        except:
            pass
