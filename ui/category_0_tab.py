# ui/category_0_tab.py - Виджет вкладки для Категории 0.
# Реализует интерфейс для расчета расхода по балансовому методу.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QGroupBox
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_0 import Category0Calculator

class Category0Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 0 "Расчет расхода по балансу".
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.calculator = Category0Calculator()
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Группа для ввода данных ---
        input_group = QGroupBox("Расчет фактического расхода ресурса (Формула 1)")
        form_layout = QFormLayout(input_group)

        self.input_postuplenie = self._create_line_edit((0.0, 1e12, 6), "Масса поступившего ресурса")
        form_layout.addRow("Поступление (M_пост):", self.input_postuplenie)

        self.input_otgruzka = self._create_line_edit((0.0, 1e12, 6), "Масса отгруженного ресурса")
        form_layout.addRow("Отгрузка (M_отгр):", self.input_otgruzka)

        self.input_zapas_nachalo = self._create_line_edit((0.0, 1e12, 6), "Запас на начало периода")
        form_layout.addRow("Запас на начало (M_запас_нач):", self.input_zapas_nachalo)

        self.input_zapas_konets = self._create_line_edit((0.0, 1e12, 6), "Запас на конец периода")
        form_layout.addRow("Запас на конец (M_запас_кон):", self.input_zapas_konets)

        main_layout.addWidget(input_group)

        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать расход")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Расход (M_расход): ...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_line_edit(self, validator_params, placeholder=""):
        """Вспомогательная функция для создания поля ввода с валидатором."""
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        validator = QDoubleValidator(*validator_params, self)
        validator.setLocale(self.c_locale)
        line_edit.setValidator(validator)
        return line_edit

    def _get_float(self, line_edit, field_name):
        """Вспомогательная функция для получения числового значения из поля ввода."""
        text = line_edit.text().replace(',', '.')
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        """Выполняет расчет на основе введенных данных."""
        try:
            postuplenie = self._get_float(self.input_postuplenie, "Поступление")
            otgruzka = self._get_float(self.input_otgruzka, "Отгрузка")
            zapas_nachalo = self._get_float(self.input_zapas_nachalo, "Запас на начало")
            zapas_konets = self._get_float(self.input_zapas_konets, "Запас на конец")

            rashod = self.calculator.calculate_consumption(
                поступление=postuplenie,
                отгрузка=otgruzka,
                запас_начало=zapas_nachalo,
                запас_конец=zapas_konets
            )

            self.result_label.setText(f"Расход (M_расход): {rashod:.4f} тонн (или тыс. м³)")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Расход (M_расход): Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Расход (M_расход): Ошибка")