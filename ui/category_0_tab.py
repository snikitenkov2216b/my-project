# ui/category_0_tab.py - Виджет вкладки для Категории 0.
# Код обновлен для приема калькулятора из фабрики и для логирования.
# Комментарии на русском. Поддержка UTF-8.

import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QGroupBox,
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_0 import Category0Calculator


class Category0Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 0 "Расчет расхода по балансу".
    """

    def __init__(self, calculator: Category0Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        input_group = QGroupBox("Расчет фактического расхода ресурса (Формула 1)")
        form_layout = QFormLayout(input_group)

        self.input_postuplenie = self._create_line_edit(
            "Масса или объем поступившего ресурса (тонны или тыс. м³)"
        )
        self.input_postuplenie.setToolTip(
            "Введите общее количество ресурса, поступившего в организацию за отчетный период."
        )
        form_layout.addRow("Поступление (M_пост):", self.input_postuplenie)

        self.input_otgruzka = self._create_line_edit(
            "Масса или объем отгруженного ресурса (тонны или тыс. м³)"
        )
        self.input_otgruzka.setToolTip(
            "Введите общее количество ресурса, отгруженного на сторону за отчетный период."
        )
        form_layout.addRow("Отгрузка (M_отгр):", self.input_otgruzka)

        self.input_zapas_nachalo = self._create_line_edit(
            "Запас на начало отчетного периода"
        )
        self.input_zapas_nachalo.setToolTip(
            "Введите количество ресурса на складах организации на начало периода."
        )
        form_layout.addRow("Запас на начало (M_запас_нач):", self.input_zapas_nachalo)

        self.input_zapas_konets = self._create_line_edit(
            "Запас на конец отчетного периода"
        )
        self.input_zapas_konets.setToolTip(
            "Введите количество ресурса на складах организации на конец периода."
        )
        form_layout.addRow("Запас на конец (M_запас_кон):", self.input_zapas_konets)

        main_layout.addWidget(input_group)

        self.calculate_button = QPushButton("Рассчитать расход")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(
            self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        self.result_label = QLabel("Расход (M_расход): ...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_line_edit(self, placeholder=""):
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        validator = QDoubleValidator(-1e12, 1e12, 6, self)
        validator.setLocale(self.c_locale)
        line_edit.setValidator(validator)
        return line_edit

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        try:
            postuplenie = self._get_float(self.input_postuplenie, "Поступление")
            otgruzka = self._get_float(self.input_otgruzka, "Отгрузка")
            zapas_nachalo = self._get_float(self.input_zapas_nachalo, "Запас на начало")
            zapas_konets = self._get_float(self.input_zapas_konets, "Запас на конец")

            rashod = self.calculator.calculate_consumption(
                поступление=postuplenie,
                отгрузка=otgruzka,
                запас_начало=zapas_nachalo,
                запас_конец=zapas_konets,
            )

            self.result_label.setText(
                f"Расход (M_расход): {rashod:.4f} тонн (или тыс. м³)"
            )
            logging.info(f"Category 0 calculation successful: rashod={rashod}")

        except ValueError as e:
            logging.error(f"Category 0 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Расход (M_расход): Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 0 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(
                self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}"
            )
            self.result_label.setText("Расход (M_расход): Ошибка")
