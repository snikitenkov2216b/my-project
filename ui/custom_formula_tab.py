# ui/custom_formula_tab.py
# Вкладка для создания, визуализации и расчета пользовательских формул в формате LaTeX.
# Комментарии на русском. Поддержка UTF-8.

import logging
import json
import matplotlib.pyplot as plt
from sympy import Symbol
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel,
    QMessageBox, QGroupBox, QScrollArea, QHBoxLayout, QFileDialog
)
from PyQt6.QtGui import QPixmap, QImage, QDoubleValidator
from PyQt6.QtCore import Qt, QLocale, QTimer

from calculations.custom_formula_evaluator import CustomFormulaEvaluator

class CustomFormulaTab(QWidget):
    """
    Класс виджета-вкладки для создания и расчета пользовательских формул с LaTeX.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.evaluator = CustomFormulaEvaluator()
        self.variable_widgets = {}
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        
        # Таймер для отложенного рендеринга формулы
        self.render_timer = QTimer(self)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self._render_formula)
        
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. Блок управления
        management_layout = QHBoxLayout()
        self.load_button = QPushButton("Загрузить")
        self.load_button.clicked.connect(self._load_formula)
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self._save_formula)
        management_layout.addWidget(self.load_button)
        management_layout.addWidget(self.save_button)
        main_layout.addLayout(management_layout)

        # 2. Блок ввода и отображения формулы
        formula_group = QGroupBox("Редактор формул")
        formula_group_layout = QVBoxLayout(formula_group)
        
        formula_hbox = QHBoxLayout()
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("Введите формулу в формате LaTeX...")
        self.formula_input.textChanged.connect(self._on_text_changed)
        
        self.help_button = QPushButton("?")
        self.help_button.setFixedSize(25, 25)
        self.help_button.clicked.connect(self._show_help)
        
        formula_hbox.addWidget(QLabel("LaTeX:"))
        formula_hbox.addWidget(self.formula_input)
        formula_hbox.addWidget(self.help_button)
        formula_group_layout.addLayout(formula_hbox)

        self.formula_display = QLabel("Предпросмотр формулы появится здесь...")
        self.formula_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formula_display.setMinimumHeight(80)
        self.formula_display.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        formula_group_layout.addWidget(self.formula_display)
        
        self.analyze_button = QPushButton("Проанализировать и создать поля для переменных")
        self.analyze_button.clicked.connect(self._analyze_formula)
        formula_group_layout.addWidget(self.analyze_button)
        
        main_layout.addWidget(formula_group)

        # 3. Блок переменных (динамический)
        variables_group = QGroupBox("Переменные")
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.variables_layout = QFormLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        variables_group_layout = QVBoxLayout(variables_group)
        variables_group_layout.addWidget(scroll_area)
        main_layout.addWidget(variables_group)
        
        # 4. Блок результата
        calculation_layout = QHBoxLayout()
        self.calculate_button = QPushButton("Рассчитать")
        self.calculate_button.clicked.connect(self._perform_calculation)
        self.result_label = QLabel("Результат: ...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        calculation_layout.addWidget(self.result_label, 1, Qt.AlignmentFlag.AlignLeft)
        calculation_layout.addWidget(self.calculate_button, 0, Qt.AlignmentFlag.AlignRight)
        main_layout.addLayout(calculation_layout)

    def _on_text_changed(self):
        """Запускает таймер для рендеринга через 500 мс после прекращения ввода."""
        self.render_timer.start(500)

    def _render_formula(self):
        """Отображает LaTeX формулу как изображение."""
        formula_latex = self.formula_input.text()
        if not formula_latex:
            self.formula_display.setText("Предпросмотр формулы появится здесь...")
            return

        try:
            # Создаем фигуру matplotlib в памяти
            fig, ax = plt.subplots(figsize=(4, 1), dpi=150)
            ax.text(0.5, 0.5, f"${formula_latex}$", size=15, ha='center', va='center')
            ax.axis('off')
            fig.tight_layout()

            # Сохраняем изображение в буфер
            fig.canvas.draw()
            buf = fig.canvas.buffer_rgba()
            plt.close(fig)

            # Преобразуем в QImage и отображаем
            q_image = QImage(buf, buf.shape[1], buf.shape[0], QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(q_image)
            self.formula_display.setPixmap(pixmap)

        except Exception as e:
            self.formula_display.setText(f"Ошибка рендеринга:\n{e}")
            logging.warning(f"Ошибка рендеринга LaTeX: {e}")

    def _analyze_formula(self):
        """Анализирует формулу и создает поля для переменных."""
        formula = self.formula_input.text()
        if not formula:
            QMessageBox.warning(self, "Ошибка", "Поле формулы не может быть пустым.")
            return

        # Очистка старых полей
        for label, line_edit in self.variable_widgets.values():
            self.variables_layout.removeRow(line_edit)
            label.deleteLater()
            line_edit.deleteLater()
        self.variable_widgets.clear()

        # Парсинг и создание новых полей
        try:
            variable_symbols = self.evaluator.parse_variables(formula)
            if not variable_symbols:
                 QMessageBox.information(self, "Анализ", "Переменные не найдены.")
            
            for symbol in sorted(variable_symbols, key=str):
                name = str(symbol)
                label = QLabel(f"{name}:")
                line_edit = QLineEdit()
                validator = QDoubleValidator(-1e12, 1e12, 6, self)
                validator.setLocale(self.c_locale)
                line_edit.setValidator(validator)
                self.variables_layout.addRow(label, line_edit)
                self.variable_widgets[name] = (label, line_edit)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка анализа", f"Не удалось проанализировать формулу: {e}")

    def _perform_calculation(self):
        """Собирает значения и выполняет расчет."""
        try:
            formula = self.formula_input.text()
            if not formula:
                raise ValueError("Формула не введена.")

            variables = {}
            for name, (_, line_edit) in self.variable_widgets.items():
                value_str = line_edit.text().replace(",", ".")
                if not value_str:
                    raise ValueError(f"Не заполнено значение для переменной '{name}'.")
                variables[name] = float(value_str)

            result = self.evaluator.evaluate(formula, variables)
            self.result_label.setText(f"Результат: {result:.6f}")
            logging.info(f"Custom formula calculation successful: Result={result}")

        except (ValueError, NameError, TypeError) as e:
            logging.error(f"Custom Formula Calculation - Error: {e}")
            QMessageBox.warning(self, "Ошибка вычисления", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(f"Custom Formula Calculation - Unexpected error: {e}", exc_info=True)
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")
            
    def _load_formula(self):
        """Загружает формулу из JSON файла."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Загрузить формулу", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.formula_input.setText(data.get("formula", ""))
                    self._analyze_formula() # Сразу анализируем
                    QMessageBox.information(self, "Успех", f"Формула '{data.get('name', 'Без имени')}' загружена.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка загрузки", f"Не удалось прочитать файл: {e}")

    def _save_formula(self):
        """Сохраняет формулу в JSON файл."""
        formula = self.formula_input.text()
        if not formula:
            QMessageBox.warning(self, "Ошибка", "Нечего сохранять. Введите формулу.")
            return

        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить формулу", "", "JSON Files (*.json)")
        if file_name:
            try:
                # Простое имя для примера, можно добавить поле для ввода имени
                formula_name = "Моя формула" 
                data = {"name": formula_name, "formula": formula}
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "Успех", "Формула успешно сохранена.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось сохранить файл: {e}")
    
    def _show_help(self):
        """Показывает окно помощи с синтаксисом и функциями."""
        help_text = """
        <b>Как писать формулы (синтаксис LaTeX):</b>
        <p>Используйте стандартные математические операторы и команды LaTeX:</p>
        <ul>
            <li>Сложение: <b>+</b>, Вычитание: <b>-</b>, Скобки: <b>()</b></li>
            <li>Умножение: <b>*</b> или пробел (например, <b>2 a</b>)</li>
            <li>Деление: <b>\frac{a}{b}</b></li>
            <li>Возведение в степень: <b>a^b</b> (для одного символа) или <b>a^{b+c}</b></li>
            <li>Квадратный корень: <b>\sqrt{x}</b></li>
        </ul>
        <p><b>Доступные функции (в разработке):</b></p>
        <ul>
            <li>Суммирование: <b>\sum_{i=1}^{n} x_i</b> (пока не поддерживается)</li>
            <li>Логарифмы: <b>\ln(x)</b>, <b>\log_{10}(x)</b></li>
            <li>Тригонометрия: <b>\sin(x)</b>, <b>\cos(x)</b>, <b>\tan(x)</b></li>
        </ul>
        <p><b>Пример:</b> \\frac{\\sqrt{a^2 + b^2}}{c}</p>
        """
        QMessageBox.information(self, "Справка по LaTeX-формулам", help_text)