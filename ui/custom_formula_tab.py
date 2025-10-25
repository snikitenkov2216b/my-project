# ui/custom_formula_tab.py
"""
Вкладка для работы с пользовательскими формулами расчета парниковых газов.
Полностью переработанная версия 2.0 с улучшенным UX.

Особенности:
- Визуализация формул с помощью LaTeX
- Динамическое создание полей ввода
- Блоки суммирования с индексацией
- Библиотека сохраненных формул
- Экспорт результатов

Автор: GHG Calculator Team
Версия: 2.0
"""

import logging
import json
import re
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # Без GUI
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel,
    QMessageBox, QGroupBox, QScrollArea, QHBoxLayout, QFileDialog, 
    QSpinBox, QInputDialog, QTextEdit
)
from PyQt6.QtGui import QPixmap, QImage, QDoubleValidator
from PyQt6.QtCore import Qt, QLocale, QTimer

from calculations.custom_formula_evaluator import CustomFormulaEvaluator
from paths import get_user_data_dir


# Путь к файлу библиотеки формул
LIBRARY_FILE = get_user_data_dir() / "formulas_library.json"


class CustomFormulaTab(QWidget):
    """Вкладка для создания и вычисления пользовательских формул."""
    
    def __init__(self, parent=None):
        """Инициализация вкладки."""
        super().__init__(parent)
        
        # Основные компоненты
        self.evaluator = CustomFormulaEvaluator()
        self.logger = logging.getLogger(__name__)
        
        # Хранилища данных
        self.variable_widgets = {}  # {имя_переменной: (QLabel, QLineEdit)}
        self.sum_blocks = []  # Список блоков суммирования
        
        # Результаты расчета
        self.last_calculation_result = None
        self.last_calculation_details = None
        
        # Локаль для валидации чисел
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        
        # Таймер для отложенного рендеринга формулы
        self.render_timer = QTimer(self)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self._render_formula)
        
        self._init_ui()
        self.logger.info("CustomFormulaTab initialized")

    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        main_layout = QVBoxLayout(self)
        
        # Прокручиваемая область для всех элементов
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        main_widget = QWidget()
        self.form_container_layout = QVBoxLayout(main_widget)
        self.form_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.form_container_layout.setSpacing(15)
        
        scroll_area.setWidget(main_widget)
        main_layout.addWidget(scroll_area)
        
        # === 1. БЛОК УПРАВЛЕНИЯ БИБЛИОТЕКОЙ ===
        self._create_library_management_block()
        
        # === 2. БЛОК ВВОДА И ВИЗУАЛИЗАЦИИ ФОРМУЛЫ ===
        self._create_formula_input_block()
        
        # === 3. КОНТЕЙНЕР ДЛЯ ДИНАМИЧЕСКИХ БЛОКОВ ===
        self.dynamic_blocks_layout = QVBoxLayout()
        self.dynamic_blocks_layout.setSpacing(10)
        self.form_container_layout.addLayout(self.dynamic_blocks_layout)
        
        # === 4. УПРАВЛЕНИЕ БЛОКАМИ СУММИРОВАНИЯ ===
        self._create_sum_block_controls()
        
        # === 5. БЛОК РЕЗУЛЬТАТОВ И ЭКСПОРТА ===
        self._create_results_block()

    def _create_library_management_block(self):
        """Создает блок управления библиотекой формул."""
        management_group = QGroupBox("📚 Библиотека формул")
        management_layout = QHBoxLayout(management_group)
        
        self.load_button = QPushButton("📂 Загрузить из библиотеки")
        self.load_button.setToolTip("Загрузить ранее сохраненную формулу")
        self.load_button.clicked.connect(self._load_formula_from_library)
        
        self.save_button = QPushButton("💾 Сохранить в библиотеку")
        self.save_button.setToolTip("Сохранить текущую формулу для повторного использования")
        self.save_button.clicked.connect(self._save_formula_to_library)
        
        management_layout.addWidget(self.load_button)
        management_layout.addWidget(self.save_button)
        management_layout.addStretch()
        
        self.form_container_layout.addWidget(management_group)

    def _create_formula_input_block(self):
        """Создает блок ввода и отображения формулы."""
        formula_group = QGroupBox("📝 Формула для расчета")
        formula_layout = QVBoxLayout(formula_group)
        
        # Поле ввода формулы
        input_layout = QHBoxLayout()
        
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText(
            "Пример: E_CO2_y = Sum_Block_1 + C_factor * 3.66"
        )
        self.formula_input.textChanged.connect(self._on_formula_text_changed)
        self.formula_input.setMinimumHeight(35)
        
        self.help_button = QPushButton("❓")
        self.help_button.setFixedSize(35, 35)
        self.help_button.setToolTip("Справка по синтаксису формул")
        self.help_button.clicked.connect(self._show_help_dialog)
        
        input_layout.addWidget(QLabel("<b>Формула:</b>"))
        input_layout.addWidget(self.formula_input, 1)
        input_layout.addWidget(self.help_button)
        
        formula_layout.addLayout(input_layout)
        
        # Область предпросмотра формулы (LaTeX рендеринг)
        preview_label = QLabel("<b>Предпросмотр:</b>")
        formula_layout.addWidget(preview_label)
        
        self.formula_display = QLabel()
        self.formula_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formula_display.setMinimumHeight(100)
        self.formula_display.setStyleSheet(
            "QLabel { background-color: white; border: 1px solid #ccc; "
            "border-radius: 5px; padding: 10px; }"
        )
        self.formula_display.setText("Введите формулу для предпросмотра...")
        formula_layout.addWidget(self.formula_display)
        
        # Кнопка анализа формулы
        self.analyze_button = QPushButton("🔍 Проанализировать и создать поля переменных")
        self.analyze_button.setToolTip(
            "Автоматически создает поля ввода для всех переменных в формуле"
        )
        self.analyze_button.clicked.connect(self._analyze_and_create_fields)
        self.analyze_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-weight: bold; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        formula_layout.addWidget(self.analyze_button)
        
        self.form_container_layout.addWidget(formula_group)

    def _create_sum_block_controls(self):
        """Создает кнопку добавления блока суммирования."""
        self.add_sum_block_button = QPushButton("➕ Добавить блок суммирования")
        self.add_sum_block_button.setToolTip(
            "Добавить блок для расчета суммы: Σ(выражение_j) для j=1..n"
        )
        self.add_sum_block_button.clicked.connect(self._add_sum_block)
        self.add_sum_block_button.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "font-weight: bold; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        self.form_container_layout.addWidget(self.add_sum_block_button)

    def _create_results_block(self):
        """Создает блок отображения результатов и экспорта."""
        results_group = QGroupBox("📊 Результаты расчета")
        results_layout = QVBoxLayout(results_group)
        
        # Результат расчета
        self.result_label = QLabel("Результат: <i>не рассчитан</i>")
        self.result_label.setStyleSheet(
            "QLabel { font-size: 16px; font-weight: bold; "
            "padding: 10px; background-color: #f0f0f0; "
            "border-radius: 5px; }"
        )
        results_layout.addWidget(self.result_label)
        
        # Кнопки действий
        buttons_layout = QHBoxLayout()
        
        self.calculate_button = QPushButton("🧮 Рассчитать")
        self.calculate_button.setToolTip("Выполнить расчет по введенной формуле")
        self.calculate_button.clicked.connect(self._perform_calculation)
        self.calculate_button.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; "
            "font-weight: bold; padding: 10px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #e68900; }"
        )
        
        self.export_button = QPushButton("📤 Экспортировать результат")
        self.export_button.setToolTip("Сохранить результаты расчета в файл")
        self.export_button.clicked.connect(self._export_results)
        self.export_button.setEnabled(False)
        self.export_button.setStyleSheet(
            "QPushButton { background-color: #607D8B; color: white; "
            "padding: 10px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #546E7A; }"
            "QPushButton:disabled { background-color: #cccccc; }"
        )
        
        buttons_layout.addWidget(self.calculate_button, 1)
        buttons_layout.addWidget(self.export_button, 1)
        
        results_layout.addLayout(buttons_layout)
        self.form_container_layout.addWidget(results_group)

    # ==================== ОСНОВНЫЕ МЕТОДЫ ====================

    def _on_formula_text_changed(self):
        """Обработчик изменения текста формулы (отложенный рендеринг)."""
        self.render_timer.start(500)  # Задержка 500 мс

    def _render_formula(self):
        """Рендеринг формулы в LaTeX с помощью matplotlib."""
        formula_text = self.formula_input.text().strip()
        
        if not formula_text:
            self.formula_display.setText("Введите формулу для предпросмотра...")
            return
        
        try:
            # Преобразуем формулу в LaTeX формат
            formula_latex = self._convert_to_latex(formula_text)
            
            # Создаем изображение формулы
            fig, ax = plt.subplots(figsize=(8, 1.5), dpi=120)
            ax.text(0.5, 0.5, f"${formula_latex}$", size=14, 
                   ha='center', va='center')
            ax.axis('off')
            fig.tight_layout(pad=0.1)
            
            # Конвертируем в QImage
            fig.canvas.draw()
            buf = fig.canvas.buffer_rgba()
            plt.close(fig)
            
            q_image = QImage(
                buf, buf.shape[1], buf.shape[0], 
                QImage.Format.Format_RGBA8888
            )
            self.formula_display.setPixmap(QPixmap.fromImage(q_image))
            
        except Exception as e:
            self.logger.warning(f"Ошибка рендеринга LaTeX: {e}")
            self.formula_display.setText(f"⚠ Ошибка отображения формулы")

    def _convert_to_latex(self, formula_text: str) -> str:
        """Конвертирует формулу в LaTeX формат."""
        latex = formula_text
        
        # Преобразование переменных с индексами
        def to_latex_var(var_name):
            parts = var_name.split('_')
            if len(parts) > 1:
                base = parts[0]
                indices = ','.join([
                    f"\\text{{{p}}}" if not p.isdigit() and p != 'j' else p 
                    for p in parts[1:]
                ])
                return f"{base}_{{{indices}}}"
            return var_name
        
        # Находим все переменные
        all_vars = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', latex)
        
        # Обрабатываем блоки суммирования
        for var in sorted(set(all_vars), key=len, reverse=True):
            if var.lower().startswith("sum_block_"):
                block = next((b for b in self.sum_blocks if b["name"] == var), None)
                if block and block["expression_input"] and block["item_count"]:
                    sum_expr = block["expression_input"].text() or "..."
                    n = block["item_count"].value()
                    
                    # Конвертируем выражение суммы
                    sum_expr_latex = re.sub(
                        r'([a-zA-Z_][a-zA-Z0-9_]*)', 
                        lambda m: to_latex_var(m.group(1)), 
                        sum_expr.replace('*', r' \times ')
                    )
                    
                    sum_block_latex = f"\\sum_{{j=1}}^{{{n}}} \\left({sum_expr_latex}\\right)"
                    latex = latex.replace(var, sum_block_latex)
            else:
                # Обычные переменные
                latex = re.sub(r'\b' + var + r'\b', to_latex_var(var), latex)
        
        # Математические операции
        latex = latex.replace('*', r' \times ')
        latex = re.sub(r'(\S+)\s*\*\*\s*(\S+)', r'{\1}^{\2}', latex)
        latex = re.sub(r'(\S+)\s*/\s*(\S+)', r'\\frac{\1}{\2}', latex)
        
        return latex

    def _analyze_and_create_fields(self):
        """Анализирует формулу и создает поля для простых переменных."""
        formula = self.formula_input.text().strip()
        
        if not formula:
            QMessageBox.warning(
                self, "Ошибка", 
                "Сначала введите формулу для анализа."
            )
            return
        
        try:
            # Очищаем старые поля простых переменных
            self._clear_simple_variable_fields()
            
            # Парсим переменные
            all_variables = self.evaluator.parse_variables(formula)
            
            # Фильтруем: оставляем только "простые" переменные (не Sum_Block_*)
            simple_vars = {
                v for v in all_variables 
                if not v.lower().startswith('sum_block_')
            }
            
            if not simple_vars:
                QMessageBox.information(
                    self, "Информация",
                    "В формуле нет простых переменных. "
                    "Возможно, используются только блоки суммирования."
                )
                return
            
            # Создаем группу для простых переменных
            variables_group = QGroupBox("🔢 Значения переменных")
            variables_layout = QFormLayout(variables_group)
            variables_layout.setSpacing(10)
            
            for var_name in sorted(simple_vars):
                label = QLabel(f"<b>{var_name}:</b>")
                label.setToolTip(f"Введите значение для переменной {var_name}")
                
                line_edit = QLineEdit()
                line_edit.setPlaceholderText("0.0")
                
                # Валидация: только числа с плавающей точкой
                validator = QDoubleValidator(-1e12, 1e12, 6, self)
                validator.setLocale(self.c_locale)
                line_edit.setValidator(validator)
                
                variables_layout.addRow(label, line_edit)
                self.variable_widgets[var_name] = (label, line_edit)
            
            self.dynamic_blocks_layout.addWidget(variables_group)
            self.logger.info(f"Created fields for {len(simple_vars)} variables")
            
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка анализа",
                f"Не удалось проанализировать формулу:\n{e}"
            )

    def _clear_simple_variable_fields(self):
        """Очищает только поля простых переменных (не затрагивая блоки сумм)."""
        for i in reversed(range(self.dynamic_blocks_layout.count())):
            widget = self.dynamic_blocks_layout.itemAt(i).widget()
            if widget and not widget.objectName().startswith("Sum_Block"):
                widget.deleteLater()
        
        self.variable_widgets.clear()

    def _add_sum_block(self, expression="", item_count=1):
        """Добавляет блок суммирования."""
        block_id = len(self.sum_blocks) + 1
        block_name = f"Sum_Block_{block_id}"
        
        # Создаем группу для блока
        sum_group = QGroupBox(f"Σ Блок суммирования: {block_name}")
        sum_group.setObjectName(block_name)
        sum_group.setStyleSheet(
            "QGroupBox { font-weight: bold; border: 2px solid #2196F3; "
            "border-radius: 5px; margin-top: 10px; padding: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; "
            "left: 10px; padding: 0 5px; }"
        )
        
        block_layout = QVBoxLayout(sum_group)
        
        # Кнопка удаления блока
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
        remove_button = QPushButton("🗑 Удалить блок")
        remove_button.setToolTip("Удалить этот блок суммирования")
        remove_button.setFixedSize(120, 30)
        remove_button.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; "
            "border-radius: 4px; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        
        def remove_this_block():
            self._remove_sum_block(block_name)
        
        remove_button.clicked.connect(remove_this_block)
        header_layout.addWidget(remove_button)
        block_layout.addLayout(header_layout)
        
        # Настройки блока
        settings_layout = QFormLayout()
        settings_layout.setSpacing(8)
        
        # Выражение для суммирования
        expression_input = QLineEdit(expression)
        expression_input.setPlaceholderText("Пример: FC_j * EF_j * OF_j")
        expression_input.setToolTip(
            "Выражение с индексом '_j', который будет заменен на _1, _2, ..., _n"
        )
        expression_input.textChanged.connect(self._on_formula_text_changed)
        settings_layout.addRow("<b>Выражение (с '_j'):</b>", expression_input)
        
        # Количество элементов
        item_count_spinbox = QSpinBox()
        item_count_spinbox.setRange(1, 100)
        item_count_spinbox.setValue(item_count)
        item_count_spinbox.setToolTip("Количество элементов в сумме (n)")
        item_count_spinbox.valueChanged.connect(self._on_formula_text_changed)
        settings_layout.addRow("<b>Количество элементов (n):</b>", item_count_spinbox)
        
        # Кнопка генерации полей
        generate_button = QPushButton("⚡ Сгенерировать поля для элементов")
        generate_button.setToolTip(
            "Создать поля ввода для каждого элемента суммы"
        )
        generate_button.setStyleSheet(
            "QPushButton { background-color: #9C27B0; color: white; "
            "padding: 8px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #7B1FA2; }"
        )
        
        settings_layout.addRow("", generate_button)
        block_layout.addLayout(settings_layout)
        
        # Контейнер для строк элементов
        rows_container = QWidget()
        rows_layout = QVBoxLayout(rows_container)
        rows_layout.setSpacing(5)
        rows_layout.setContentsMargins(0, 10, 0, 0)
        block_layout.addWidget(rows_container)
        
        # Сохраняем данные блока
        block_data = {
            "name": block_name,
            "group_widget": sum_group,
            "expression_input": expression_input,
            "item_count": item_count_spinbox,
            "rows_layout": rows_layout,
            "variable_rows": []
        }
        
        # Привязываем обработчик генерации
        def generate_fields():
            self._generate_sum_block_fields(block_data)
        
        generate_button.clicked.connect(generate_fields)
        
        self.sum_blocks.append(block_data)
        self.dynamic_blocks_layout.addWidget(sum_group)
        
        self.logger.info(f"Added {block_name}")

    def _remove_sum_block(self, block_name: str):
        """Удаляет блок суммирования."""
        block_to_remove = next(
            (b for b in self.sum_blocks if b["name"] == block_name), 
            None
        )
        
        if block_to_remove:
            block_to_remove["group_widget"].deleteLater()
            self.sum_blocks.remove(block_to_remove)
            self.logger.info(f"Removed {block_name}")
            self._on_formula_text_changed()

    def _generate_sum_block_fields(self, block_data: dict):
        """Генерирует поля ввода для элементов блока суммирования."""
        expression = block_data["expression_input"].text().strip()
        
        if not expression:
            QMessageBox.warning(
                self, "Ошибка",
                "Сначала введите выражение для блока суммирования."
            )
            return
        
        try:
            # Очищаем старые строки
            for row in block_data["variable_rows"]:
                row["widget"].deleteLater()
            block_data["variable_rows"].clear()
            
            # Парсим переменные из выражения
            base_vars = self.evaluator.parse_variables(expression)
            
            if not base_vars:
                QMessageBox.warning(
                    self, "Ошибка",
                    "В выражении не найдены переменные."
                )
                return
            
            # Генерируем поля для каждого элемента
            count = block_data["item_count"].value()
            
            for i in range(1, count + 1):
                row_widget = QWidget()
                row_widget.setStyleSheet(
                    "QWidget { background-color: #f9f9f9; "
                    "border: 1px solid #ddd; border-radius: 3px; "
                    "padding: 5px; }"
                )
                
                row_layout = QHBoxLayout(row_widget)
                row_layout.setSpacing(8)
                
                # Заголовок элемента
                element_label = QLabel(f"<b>Элемент {i}:</b>")
                element_label.setMinimumWidth(80)
                row_layout.addWidget(element_label)
                
                # Поля для переменных
                row_inputs = {}
                
                for var in sorted(base_vars):
                    # Заменяем '_j' на '_i'
                    indexed_var_name = var.replace('_j', f'_{i}')
                    
                    var_label = QLabel(f"{indexed_var_name}:")
                    var_label.setMinimumWidth(60)
                    
                    line_edit = QLineEdit()
                    line_edit.setPlaceholderText("0.0")
                    line_edit.setMinimumWidth(80)
                    
                    validator = QDoubleValidator(-1e12, 1e12, 6, self)
                    validator.setLocale(self.c_locale)
                    line_edit.setValidator(validator)
                    
                    row_layout.addWidget(var_label)
                    row_layout.addWidget(line_edit)
                    
                    row_inputs[indexed_var_name] = line_edit
                
                row_layout.addStretch()
                
                block_data["variable_rows"].append({
                    "widget": row_widget,
                    "inputs": row_inputs
                })
                
                block_data["rows_layout"].addWidget(row_widget)
            
            self.logger.info(
                f"Generated {count} rows for {block_data['name']}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка",
                f"Не удалось сгенерировать поля:\n{e}"
            )

    def _perform_calculation(self):
        """Выполняет расчет по формуле."""
        formula = self.formula_input.text().strip()
        
        if not formula:
            QMessageBox.warning(
                self, "Ошибка",
                "Введите формулу для расчета."
            )
            return
        
        try:
            # Собираем значения простых переменных
            variables = {}
            
            for var_name, (_, line_edit) in self.variable_widgets.items():
                value = self._get_float_value(line_edit, var_name)
                variables[var_name] = value
            
            # Детали расчета для экспорта
            calculation_details = {
                "formula": formula,
                "timestamp": datetime.now().isoformat(),
                "simple_variables": dict(variables),
                "sum_blocks": []
            }
            
            # Обрабатываем блоки суммирования
            for block in self.sum_blocks:
                expression = block["expression_input"].text().strip()
                
                if not expression:
                    raise ValueError(
                        f"Не заполнено выражение для {block['name']}"
                    )
                
                # Собираем значения для каждого элемента
                variables_by_index = []
                
                for row in block["variable_rows"]:
                    row_values = {
                        name: self._get_float_value(widget, name)
                        for name, widget in row["inputs"].items()
                    }
                    variables_by_index.append(row_values)
                
                if not variables_by_index:
                    raise ValueError(
                        f"Не сгенерированы поля для {block['name']}"
                    )
                
                # Вычисляем сумму
                sum_result = self.evaluator.evaluate_sum_block(
                    expression, variables_by_index
                )
                
                # Сохраняем результат блока
                variables[block["name"]] = sum_result
                
                # Добавляем детали в отчет
                calculation_details["sum_blocks"].append({
                    "name": block["name"],
                    "expression": expression,
                    "items": variables_by_index,
                    "sum_result": sum_result
                })
            
            # Финальный расчет
            result = self.evaluator.evaluate(formula, variables)
            
            # Отображаем результат
            self.result_label.setText(
                f"<span style='color: green;'>Результат: {result:.6f}</span>"
            )
            
            # Сохраняем для экспорта
            self.last_calculation_result = result
            self.last_calculation_details = calculation_details
            self.export_button.setEnabled(True)
            
            self.logger.info(f"Calculation successful: {result:.6f}")
            
        except Exception as e:
            error_msg = str(e)
            self.result_label.setText(
                f"<span style='color: red;'>Ошибка: {error_msg}</span>"
            )
            self.export_button.setEnabled(False)
            
            QMessageBox.critical(
                self, "Ошибка расчета",
                f"Произошла ошибка при вычислении:\n\n{error_msg}"
            )

    def _get_float_value(self, line_edit: QLineEdit, field_name: str) -> float:
        """Извлекает и валидирует числовое значение из поля ввода."""
        text = line_edit.text().replace(',', '.').strip()
        
        if not text:
            raise ValueError(
                f"Поле '{field_name}' не может быть пустым."
            )
        
        try:
            return float(text)
        except ValueError:
            raise ValueError(
                f"Некорректное числовое значение в поле '{field_name}': '{text}'"
            )

    def _export_results(self):
        """Экспортирует результаты расчета в текстовый файл."""
        if self.last_calculation_result is None:
            QMessageBox.warning(
                self, "Ошибка",
                "Нет результатов для экспорта. Сначала выполните расчет."
            )
            return
        
        # Диалог сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результаты расчета",
            str(get_user_data_dir() / "calculation_result.txt"),
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("ОТЧЕТ О РАСЧЕТЕ ВЫБРОСОВ ПАРНИКОВЫХ ГАЗОВ\n")
                f.write("=" * 70 + "\n\n")
                
                details = self.last_calculation_details
                
                f.write(f"Дата и время: {details['timestamp']}\n\n")
                f.write(f"Формула:\n{details['formula']}\n\n")
                
                # Простые переменные
                if details['simple_variables']:
                    f.write("Значения переменных:\n")
                    f.write("-" * 40 + "\n")
                    for var, value in details['simple_variables'].items():
                        f.write(f"  {var:20s} = {value:12.6f}\n")
                    f.write("\n")
                
                # Блоки суммирования
                if details['sum_blocks']:
                    f.write("Блоки суммирования:\n")
                    f.write("-" * 40 + "\n")
                    
                    for block in details['sum_blocks']:
                        f.write(f"\n{block['name']}:\n")
                        f.write(f"  Выражение: {block['expression']}\n")
                        f.write(f"  Элементы:\n")
                        
                        for i, item in enumerate(block['items'], 1):
                            f.write(f"    Элемент {i}:\n")
                            for var, val in item.items():
                                f.write(f"      {var} = {val:.6f}\n")
                        
                        f.write(f"  Сумма: {block['sum_result']:.6f}\n")
                    f.write("\n")
                
                # Итоговый результат
                f.write("=" * 70 + "\n")
                f.write(f"ИТОГОВЫЙ РЕЗУЛЬТАТ: {self.last_calculation_result:.6f}\n")
                f.write("=" * 70 + "\n")
            
            QMessageBox.information(
                self, "Успех",
                f"Результаты успешно экспортированы в:\n{file_path}"
            )
            
            self.logger.info(f"Results exported to: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка экспорта",
                f"Не удалось сохранить файл:\n{e}"
            )

    # ==================== БИБЛИОТЕКА ФОРМУЛ ====================

    def _save_formula_to_library(self):
        """Сохраняет текущую формулу в библиотеку."""
        formula = self.formula_input.text().strip()
        
        if not formula:
            QMessageBox.warning(
                self, "Ошибка",
                "Нечего сохранять. Введите формулу."
            )
            return
        
        # Запрашиваем название
        name, ok = QInputDialog.getText(
            self, "Сохранить формулу",
            "Введите название для формулы:"
        )
        
        if not ok or not name.strip():
            return
        
        # Формируем данные для сохранения
        formula_data = {
            "name": name.strip(),
            "main_formula": formula,
            "sum_blocks": [
                {
                    "name": block["name"],
                    "expression": block["expression_input"].text(),
                    "item_count": block["item_count"].value()
                }
                for block in self.sum_blocks
            ]
        }
        
        try:
            # Загружаем существующую библиотеку
            library = self._load_library()
            
            # Удаляем старую версию с таким же названием
            library = [f for f in library if f['name'] != name.strip()]
            
            # Добавляем новую формулу
            library.append(formula_data)
            
            # Сохраняем
            self._save_library(library)
            
            QMessageBox.information(
                self, "Успех",
                f"Формула '{name}' сохранена в библиотеку."
            )
            
            self.logger.info(f"Formula saved to library: {name}")
            
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка",
                f"Не удалось сохранить формулу:\n{e}"
            )

    def _load_formula_from_library(self):
        """Загружает формулу из библиотеки."""
        try:
            library = self._load_library()
            
            if not library:
                QMessageBox.information(
                    self, "Библиотека пуста",
                    "В библиотеке пока нет сохраненных формул."
                )
                return
            
            # Выбор формулы
            formula_names = [f['name'] for f in library]
            
            name, ok = QInputDialog.getItem(
                self, "Загрузить формулу",
                "Выберите формулу для загрузки:",
                formula_names, 0, False
            )
            
            if not ok:
                return
            
            # Находим выбранную формулу
            formula_data = next(
                (f for f in library if f['name'] == name), 
                None
            )
            
            if formula_data:
                self._reconstruct_ui_from_formula(formula_data)
                
                QMessageBox.information(
                    self, "Успех",
                    f"Формула '{name}' загружена."
                )
                
                self.logger.info(f"Formula loaded from library: {name}")
            
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка",
                f"Не удалось загрузить формулу:\n{e}"
            )

    def _reconstruct_ui_from_formula(self, formula_data: dict):
        """Восстанавливает UI из сохраненных данных формулы."""
        # Полная очистка
        self.formula_input.clear()
        self._clear_simple_variable_fields()
        
        # Удаляем все блоки суммирования
        for block in list(self.sum_blocks):
            self._remove_sum_block(block["name"])
        
        # Устанавливаем формулу
        self.formula_input.setText(formula_data.get("main_formula", ""))
        
        # Воссоздаем блоки суммирования
        for block_data in formula_data.get("sum_blocks", []):
            self._add_sum_block(
                expression=block_data.get("expression", ""),
                item_count=block_data.get("item_count", 1)
            )
        
        # Анализируем формулу
        self._analyze_and_create_fields()
        self._on_formula_text_changed()

    def _load_library(self) -> list:
        """Загружает библиотеку формул из файла."""
        if not LIBRARY_FILE.exists():
            return []
        
        try:
            with open(LIBRARY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_library(self, library: list):
        """Сохраняет библиотеку формул в файл."""
        LIBRARY_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(LIBRARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(library, f, ensure_ascii=False, indent=2)

    # ==================== СПРАВКА ====================

    def _show_help_dialog(self):
        """Показывает справку по использованию модуля."""
        help_text = """
        <h2>Справка по модулю "Своя формула"</h2>
        
        <h3>📌 Основные возможности</h3>
        <ul>
            <li>Создание пользовательских формул расчета выбросов ПГ</li>
            <li>Блоки суммирования для повторяющихся вычислений</li>
            <li>Визуализация формул в LaTeX формате</li>
            <li>Сохранение формул в библиотеку</li>
            <li>Экспорт результатов в файл</li>
        </ul>
        
        <h3>🔢 Синтаксис формул</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr bgcolor="#f0f0f0">
                <th>Операция</th>
                <th>Синтаксис</th>
                <th>Пример</th>
            </tr>
            <tr>
                <td>Умножение</td>
                <td>*</td>
                <td>a * b</td>
            </tr>
            <tr>
                <td>Деление</td>
                <td>/</td>
                <td>a / b</td>
            </tr>
            <tr>
                <td>Степень</td>
                <td>**</td>
                <td>a**2</td>
            </tr>
            <tr>
                <td>Скобки</td>
                <td>( )</td>
                <td>(a + b) * c</td>
            </tr>
            <tr>
                <td>Индексы</td>
                <td>_</td>
                <td>EF_CO2_y</td>
            </tr>
        </table>
        
        <h3>📊 Блоки суммирования</h3>
        <p>Для расчета суммы: Σ(выражение_j) для j=1..n</p>
        <ol>
            <li>Нажмите "Добавить блок суммирования"</li>
            <li>Введите выражение с индексом '_j' (например: FC_j * EF_j)</li>
            <li>Укажите количество элементов (n)</li>
            <li>Нажмите "Сгенерировать поля"</li>
            <li>Заполните значения для каждого элемента</li>
            <li>В основной формуле используйте имя блока (например: Sum_Block_1)</li>
        </ol>
        
        <h3>💡 Примеры формул</h3>
        <p><b>Пример 1:</b> Простая формула</p>
        <pre>E_CO2 = FC * EF * OF</pre>
        
        <p><b>Пример 2:</b> С блоком суммирования</p>
        <pre>E_total = Sum_Block_1 + C_const * 3.66</pre>
        <p>где Sum_Block_1 содержит: FC_j * EF_j * OF_j</p>
        
        <hr>
        <p><i>Для дополнительной помощи обратитесь к документации проекта.</i></p>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Справка - Своя формула")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(help_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()


# ==================== ТЕСТИРОВАНИЕ ====================

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    logging.basicConfig(level=logging.DEBUG)
    
    app = QApplication(sys.argv)
    window = CustomFormulaTab()
    window.setWindowTitle("Тест - Своя формула")
    window.resize(900, 700)
    window.show()
    
    sys.exit(app.exec())
