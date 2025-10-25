# ui/custom_formula_tab.py
# Финальная версия с удалением блоков, библиотекой формул и всеми исправлениями.
# Комментарии на русском. Поддержка UTF-8.

import logging
import json
import re
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel,
    QMessageBox, QGroupBox, QScrollArea, QHBoxLayout, QFileDialog, QSpinBox, QInputDialog
)
from PyQt6.QtGui import QPixmap, QImage, QDoubleValidator
from PyQt6.QtCore import Qt, QLocale, QTimer

from calculations.custom_formula_evaluator import CustomFormulaEvaluator
from ui.formula_library_dialog import FormulaLibraryDialog, LIBRARY_FILE

class CustomFormulaTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.evaluator = CustomFormulaEvaluator()
        self.variable_widgets = {}
        self.sum_blocks = []
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        
        self.render_timer = QTimer(self)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self._render_formula)
        
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        self.form_container_layout = QVBoxLayout(main_widget)
        self.form_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(main_widget)
        main_layout.addWidget(scroll_area)

        # 1. Блок управления
        management_layout = QHBoxLayout()
        self.load_button = QPushButton("Загрузить из библиотеки")
        self.load_button.clicked.connect(self._load_formula)
        self.save_button = QPushButton("Сохранить в библиотеку")
        self.save_button.clicked.connect(self._save_formula)
        management_layout.addWidget(self.load_button)
        management_layout.addWidget(self.save_button)
        self.form_container_layout.addLayout(management_layout)

        # 2. Блок ввода и отображения формулы
        formula_group = QGroupBox("1. Основная формула")
        formula_group_layout = QVBoxLayout(formula_group)
        formula_hbox = QHBoxLayout()
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("Пример: E_CO2_y = Sum_Block_1 + C_factor")
        self.formula_input.textChanged.connect(self._on_text_changed)
        self.help_button = QPushButton("?")
        self.help_button.setFixedSize(25, 25)
        self.help_button.clicked.connect(self._show_help)
        formula_hbox.addWidget(QLabel("Формула для расчета:"))
        formula_hbox.addWidget(self.formula_input)
        formula_hbox.addWidget(self.help_button)
        formula_group_layout.addLayout(formula_hbox)
        self.formula_display = QLabel("Предпросмотр формулы появится здесь...")
        self.formula_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formula_display.setMinimumHeight(80)
        self.formula_display.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        formula_group_layout.addWidget(self.formula_display)
        self.analyze_button = QPushButton("Проанализировать и создать поля для простых переменных")
        self.analyze_button.clicked.connect(self._analyze_formula)
        formula_group_layout.addWidget(self.analyze_button)
        self.form_container_layout.addWidget(formula_group)

        # Контейнер для динамических блоков
        self.dynamic_blocks_layout = QVBoxLayout()
        self.form_container_layout.addLayout(self.dynamic_blocks_layout)
        self.add_sum_block_button = QPushButton("Добавить блок суммирования")
        self.add_sum_block_button.clicked.connect(self._add_sum_block)
        self.form_container_layout.addWidget(self.add_sum_block_button)

        # Блок результата
        calculation_layout = QHBoxLayout()
        self.calculate_button = QPushButton("Рассчитать")
        self.calculate_button.clicked.connect(self._perform_calculation)
        self.export_button = QPushButton("Экспортировать результат")
        self.export_button.clicked.connect(self._export_result)
        self.export_button.setEnabled(False)  # Включается после расчета
        self.result_label = QLabel("Результат: ...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        calculation_layout.addWidget(self.result_label, 1, Qt.AlignmentFlag.AlignLeft)
        calculation_layout.addWidget(self.export_button, 0, Qt.AlignmentFlag.AlignRight)
        calculation_layout.addWidget(self.calculate_button, 0, Qt.AlignmentFlag.AlignRight)
        self.form_container_layout.addLayout(calculation_layout)

        # Сохраняем последний результат расчета
        self.last_calculation_result = None
        self.last_calculation_details = None

    def _add_sum_block(self, expression="", item_count=1):
        block_id = len(self.sum_blocks) + 1
        block_name = f"Sum_Block_{block_id}"
        sum_group = QGroupBox(f"Блок суммирования: {block_name}")
        sum_group.setObjectName(block_name)
        block_layout = QVBoxLayout(sum_group)

        header_layout = QHBoxLayout()
        header_layout.addStretch()
        remove_button = QPushButton("Удалить блок")
        remove_button.setFixedSize(100, 25)
        header_layout.addWidget(remove_button)
        block_layout.addLayout(header_layout)

        settings_layout = QFormLayout()
        expression_input = QLineEdit(expression)
        expression_input.setPlaceholderText("Пример: FC_j_y * EF_j_y")
        expression_input.textChanged.connect(self._on_text_changed)
        item_count_spinbox = QSpinBox()
        item_count_spinbox.setRange(1, 100)
        item_count_spinbox.setValue(item_count)
        item_count_spinbox.valueChanged.connect(self._on_text_changed)
        generate_fields_button = QPushButton("Сгенерировать поля для элементов")
        settings_layout.addRow("Выражение (с индексом '_j'):", expression_input)
        settings_layout.addRow("Количество элементов (n):", item_count_spinbox)
        settings_layout.addRow(generate_fields_button)
        block_layout.addLayout(settings_layout)

        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        scroll_content = QWidget(); dynamic_rows_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content); block_layout.addWidget(scroll_area)
        
        block_data = {
            "group": sum_group, "name": block_name, "expression_input": expression_input,
            "item_count": item_count_spinbox, "rows_layout": dynamic_rows_layout, "variable_rows": []
        }
        self.sum_blocks.append(block_data)
        
        generate_fields_button.clicked.connect(lambda: self._generate_sum_block_fields(block_data))
        remove_button.clicked.connect(lambda: self._remove_sum_block(block_data))

        self.dynamic_blocks_layout.addWidget(sum_group)
        self._on_text_changed()

    def _remove_sum_block(self, block_data_to_remove):
        block_data_to_remove["group"].deleteLater()
        self.sum_blocks.remove(block_data_to_remove)
        self._on_text_changed()

    def _generate_sum_block_fields(self, block_data):
        expression_template = block_data["expression_input"].text()
        count = block_data["item_count"].value()
        for row in block_data["variable_rows"]: row["widget"].deleteLater()
        block_data["variable_rows"].clear()
        try:
            base_vars = self.evaluator.parse_variables(expression_template)
            if not any('_j' in var for var in base_vars):
                QMessageBox.warning(self, "Ошибка", "В выражении для суммирования не найдены переменные с индексом '_j'.")
                return
            for i in range(1, count + 1):
                row_widget = QWidget(); row_layout = QHBoxLayout(row_widget)
                row_layout.addWidget(QLabel(f"<b>Элемент {i}:</b>"))
                row_inputs = {}
                for var in sorted(list(base_vars)):
                    indexed_var_name = var.replace('_j', f'_{i}')
                    line_edit = QLineEdit()
                    validator = QDoubleValidator(-1e12, 1e12, 6, self)
                    validator.setLocale(self.c_locale); line_edit.setValidator(validator)
                    line_edit.setPlaceholderText(indexed_var_name); row_layout.addWidget(line_edit)
                    row_inputs[indexed_var_name] = line_edit
                block_data["variable_rows"].append({"widget": row_widget, "inputs": row_inputs})
                block_data["rows_layout"].addWidget(row_widget)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка анализа", f"Не удалось проанализировать выражение: {e}")

    def _on_text_changed(self):
        self.render_timer.start(500)

    def _render_formula(self):
        if not self or not hasattr(self, 'formula_input') or not self.formula_input: return
        formula_text = self.formula_input.text()
        if not formula_text:
            self.formula_display.setText("Предпросмотр формулы появится здесь...")
            return
        try:
            formula_latex = formula_text
            
            def to_latex_var(var_name):
                parts = var_name.split('_')
                if len(parts) > 1:
                    indices = ','.join([f"\\text{{{p}}}" if not p.isdigit() and p != 'j' else p for p in parts[1:]])
                    return f"{parts[0]}_{{{indices}}}"
                return var_name

            all_vars = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', formula_latex)
            
            for var in sorted(list(set(all_vars)), key=len, reverse=True):
                if var.lower().startswith("sum_block_"):
                    block = next((b for b in self.sum_blocks if b["name"] == var), None)
                    if block and block["expression_input"] and block["item_count"]:
                        sum_expr_text = block["expression_input"].text() or "..."
                        n = block["item_count"].text() or "n"
                        sum_expr_latex = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)', lambda m: to_latex_var(m.group(1)), sum_expr_text.replace('*', r' \times '))
                        sum_block_latex = f"\\sum_{{j=1}}^{{{n}}} ({sum_expr_latex})"
                        formula_latex = formula_latex.replace(var, sum_block_latex)
                else:
                    formula_latex = re.sub(r'\b' + var + r'\b', to_latex_var(var), formula_latex)
            
            formula_latex = formula_latex.replace('*', r' \times ')
            formula_latex = re.sub(r'(\S+)\s*\*\*\s*(\S+)', r'{\1}^{\2}', formula_latex)
            formula_latex = re.sub(r'(\S+)\s*/\s*(\S+)', r'\\frac{\1}{\2}', formula_latex)
            
            fig, ax = plt.subplots(figsize=(6, 1.5), dpi=120)
            ax.text(0.5, 0.5, f"${formula_latex}$", size=15, ha='center', va='center')
            ax.axis('off'); fig.tight_layout(pad=0.1)
            fig.canvas.draw(); buf = fig.canvas.buffer_rgba(); plt.close(fig)
            q_image = QImage(buf, buf.shape[1], buf.shape[0], QImage.Format.Format_RGBA8888)
            self.formula_display.setPixmap(QPixmap.fromImage(q_image))
        except Exception as e:
            self.formula_display.setText(f"Ошибка рендеринга")
            logging.warning(f"Ошибка рендеринга LaTeX: {e}")

    def _analyze_formula(self):
        # Очистка только простых переменных
        for i in reversed(range(self.dynamic_blocks_layout.count())):
            widget = self.dynamic_blocks_layout.itemAt(i).widget()
            if widget and not widget.objectName().startswith("Sum_Block"):
                widget.deleteLater()
        self.variable_widgets.clear()
        
        formula = self.formula_input.text()
        if not formula: return
        
        try:
            variable_names = self.evaluator.parse_variables(formula)
            simple_vars = {v for v in variable_names if not v.lower().startswith('sum_block_')}
            if simple_vars:
                group = QGroupBox("Простые переменные"); layout = QFormLayout(group)
                self.dynamic_blocks_layout.addWidget(group)
                for name in sorted(list(simple_vars)):
                    label = QLabel(f"{name}:"); line_edit = QLineEdit()
                    validator = QDoubleValidator(-1e12, 1e12, 6, self); validator.setLocale(self.c_locale)
                    line_edit.setValidator(validator); layout.addRow(label, line_edit)
                    self.variable_widgets[name] = (label, line_edit)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка анализа", f"Не удалось проанализировать формулу: {e}")

    def _perform_calculation(self):
        try:
            formula = self.formula_input.text()
            if not formula: raise ValueError("Формула не введена.")
            variables = {name: self._get_float(widget, name) for name, (_, widget) in self.variable_widgets.items()}

            # Детали расчета для экспорта
            calculation_details = {
                "formula": formula,
                "simple_variables": dict(variables),
                "sum_blocks": []
            }

            for block in self.sum_blocks:
                expression = block["expression_input"].text()
                if not expression: raise ValueError(f"Не заполнено выражение для {block['name']}")
                variables_by_index = []
                for row in block["variable_rows"]:
                    row_values = {name: self._get_float(widget, name) for name, widget in row["inputs"].items()}
                    variables_by_index.append(row_values)
                if not variables_by_index: raise ValueError(f"Не сгенерированы или не заполнены поля для {block['name']}")
                sum_result = self.evaluator.evaluate_sum_block(expression, variables_by_index)
                variables[block["name"]] = sum_result

                # Сохраняем детали блока суммирования
                calculation_details["sum_blocks"].append({
                    "name": block["name"],
                    "expression": expression,
                    "items": variables_by_index,
                    "sum_result": sum_result
                })

            result = self.evaluator.evaluate(formula, variables)
            self.result_label.setText(f"Результат: {result:.6f}")
            logging.info(f"Custom formula calculation successful: Result={result}")

            # Сохраняем результат для экспорта
            self.last_calculation_result = result
            self.last_calculation_details = calculation_details
            self.export_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при вычислении: {e}")
            self.result_label.setText("Результат: Ошибка")
            self.export_button.setEnabled(False)

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text: raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)
            
    def _reconstruct_ui_from_formula(self, formula_data):
        # Полная очистка
        self.formula_input.clear()
        for i in reversed(range(self.dynamic_blocks_layout.count())):
            self.dynamic_blocks_layout.itemAt(i).widget().deleteLater()
        self.sum_blocks.clear()
        self.variable_widgets.clear()
        
        self.formula_input.setText(formula_data.get("main_formula", ""))
        
        for block_data in formula_data.get("sum_blocks", []):
            self._add_sum_block(
                expression=block_data.get("expression", ""),
                item_count=block_data.get("item_count", 1)
            )

        self._analyze_formula()
        self._on_text_changed()

    def _load_formula(self):
        dialog = FormulaLibraryDialog(self)
        if dialog.exec():
            selected_formula = dialog.get_selected_formula()
            if selected_formula:
                self._reconstruct_ui_from_formula(selected_formula)
                QMessageBox.information(self, "Успех", f"Формула '{selected_formula['name']}' загружена.")

    def _save_formula(self):
        main_formula = self.formula_input.text()
        if not main_formula:
            QMessageBox.warning(self, "Ошибка", "Нечего сохранять. Введите основную формулу.")
            return

        name, ok = QInputDialog.getText(self, "Сохранить формулу", "Введите название формулы:")
        if ok and name:
            formula_data = {
                "name": name,
                "main_formula": main_formula,
                "sum_blocks": [
                    {
                        "name": block["name"],
                        "expression": block["expression_input"].text(),
                        "item_count": block["item_count"].value()
                    } for block in self.sum_blocks
                ]
            }
            
            try:
                try:
                    with open(LIBRARY_FILE, 'r', encoding='utf-8') as f:
                        library = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    library = []
                
                library = [f for f in library if f['name'] != name]
                library.append(formula_data)
                
                with open(LIBRARY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(library, f, ensure_ascii=False, indent=4)
                
                QMessageBox.information(self, "Успех", f"Формула '{name}' сохранена в библиотеку.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить формулу: {e}")

    def _export_result(self):
        """Экспорт результатов расчета в текстовый файл."""
        if self.last_calculation_result is None:
            QMessageBox.warning(self, "Ошибка", "Нет результатов для экспорта. Сначала выполните расчет.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспортировать результат",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )

        if not file_path:
            return

        try:
            from datetime import datetime

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("РЕЗУЛЬТАТЫ РАСЧЕТА ПО ПОЛЬЗОВАТЕЛЬСКОЙ ФОРМУЛЕ\n")
                f.write("=" * 70 + "\n")
                f.write(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Приложение: GHG Calculator\n\n")

                details = self.last_calculation_details

                f.write("-" * 70 + "\n")
                f.write("ОСНОВНАЯ ФОРМУЛА:\n")
                f.write(f"{details['formula']}\n\n")

                if details['simple_variables']:
                    f.write("-" * 70 + "\n")
                    f.write("ПРОСТЫЕ ПЕРЕМЕННЫЕ:\n")
                    for var_name, var_value in sorted(details['simple_variables'].items()):
                        f.write(f"  {var_name:30s} = {var_value:>15.6f}\n")
                    f.write("\n")

                if details['sum_blocks']:
                    f.write("-" * 70 + "\n")
                    f.write("БЛОКИ СУММИРОВАНИЯ:\n\n")
                    for block in details['sum_blocks']:
                        f.write(f"  Блок: {block['name']}\n")
                        f.write(f"  Выражение: {block['expression']}\n")
                        f.write(f"  Количество элементов: {len(block['items'])}\n\n")

                        for idx, item_vars in enumerate(block['items'], start=1):
                            f.write(f"    Элемент {idx}:\n")
                            for var_name, var_value in sorted(item_vars.items()):
                                f.write(f"      {var_name:28s} = {var_value:>13.6f}\n")

                        f.write(f"\n  Результат суммирования: {block['sum_result']:.6f}\n\n")

                f.write("=" * 70 + "\n")
                f.write(f"ИТОГОВЫЙ РЕЗУЛЬТАТ: {self.last_calculation_result:.6f}\n")
                f.write("=" * 70 + "\n")

            QMessageBox.information(self, "Успех", f"Результаты экспортированы в файл:\n{file_path}")
            logging.info(f"Результаты расчета экспортированы: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать результаты: {e}")
            logging.error(f"Ошибка экспорта: {e}")

    def _show_help(self):
        help_text = """
        <h3>Как рассчитать формулу с суммированием (∑)</h3>
        <p><b>Шаг 1: Основная формула</b></p>
        <p>В верхнем поле введите общую структуру расчета. Вместо символа <b>∑(...)</b> используйте специальное имя, например, <b>Sum_Block_1</b>.</p>
        <p><i>Пример для вашей формулы:</i> <code>E_CO2_y = Sum_Block_1</code></p>
        <p>В окне предпросмотра вы увидите красивую формулу со знаком суммы.</p>
        
        <p><b>Шаг 2: Блок суммирования</b></p>
        <ol>
            <li>Нажмите <b>"Добавить блок суммирования"</b>.</li>
            <li><b>Выражение (с индексом '_j'):</b> Введите повторяющуюся часть формулы, используя <b>_j</b> в качестве индекса.
            <br><i>Пример для вашей формулы:</i> <code>FC_j_y * EF_CO2_j_y * OF_j_y</code></li>
            <li><b>Количество элементов (n):</b> Укажите, сколько раз нужно просуммировать выражение (например, 3, если у вас 3 вида топлива).</li>
            <li>Нажмите <b>"Сгенерировать поля для элементов"</b>.</li>
        </ol>
        
        <p><b>Шаг 3: Анализ и расчет</b></p>
        <ol>
            <li>Нажмите <b>"Проанализировать"</b>, чтобы создать поля для "простых" переменных (если они есть в основной формуле).</li>
            <li>Заполните все созданные поля числовыми значениями.</li>
            <li>Нажмите <b>"Рассчитать"</b>.</li>
        </ol>
        
        <hr>
        <b>Синтаксис для ввода и отображения</b>
        <table border="1" cellpadding="5" width="100%">
            <tr bgcolor="#f0f0f0"><th>Что писать</th><th>Как отобразится</th></tr>
            <tr><td><code>C_2</code>, <code>EF_CO2_j_y</code></td><td>$C_{2}$, $EF_{CO2,j,y}$</td></tr>
            <tr><td><code>var * 2</code></td><td>$var \\times 2$</td></tr>
            <tr><td><code>var**2</code></td><td>$var^{2}$</td></tr>
            <tr><td><code>a / b</code></td><td>$\\frac{a}{b}$</td></tr>
        </table>
        """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Справка по формулам")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(help_text)
        msg_box.exec()