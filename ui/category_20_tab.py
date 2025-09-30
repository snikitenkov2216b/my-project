# ui/category_20_tab.py - Виджет вкладки для расчетов по Категории 20.
# Код исправлен: добавлен импорт QLabel.
# Комментарии на русском. Поддержка UTF-8.

import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QStackedWidget,
    QHBoxLayout,
    QGroupBox,
    QScrollArea,
    QTextEdit,
    QLabel,  # ИСПРАВЛЕНО: Добавлен QLabel
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale
import math

from calculations.category_20 import Category20Calculator


class Category20Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 20 "Захоронение твердых отходов".
    """

    def __init__(self, calculator: Category20Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.landfill_historical_rows = []
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems(["Захоронение твердых отходов (Метод ЗПП)"])
        method_layout.addRow("Выберите тип процесса:", self.method_combobox)
        main_layout.addLayout(method_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_landfill_widget())
        main_layout.addWidget(self.stacked_widget)

        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(
            self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        self.result_label = QTextEdit()
        self.result_label.setReadOnly(True)
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.result_label.setText("Результат:...")
        main_layout.addWidget(self.result_label)

    def _create_scrollable_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(widget)
        return scroll_area, layout

    def _create_landfill_widget(self):
        scroll_area, layout = self._create_scrollable_widget()
        params_group = QGroupBox("Параметры модели затухания первого порядка (ЗПП)")
        params_layout = QFormLayout(params_group)
        self.landfill_doc_input = self._create_line_edit(
            "0.15",
            (0.0, 1.0, 6),
            "Доля способного к разложению органического углерода. Стандартное значение для ТКО - 0.15.",
        )
        params_layout.addRow(
            "Доля разлагаемого углерода (DOC, доля):", self.landfill_doc_input
        )
        self.landfill_docf_input = self._create_line_edit(
            "0.5",
            (0.0, 1.0, 6),
            "Доля DOC, который действительно разлагается. Стандартное значение - 0.5.",
        )
        params_layout.addRow("Доля DOCf (доля):", self.landfill_docf_input)
        self.landfill_mcf_input = self._create_line_edit(
            "1.0",
            (0.0, 1.0, 6),
            "Поправочный коэффициент для метана. 1.0 для анаэробных управляемых полигонов.",
        )
        params_layout.addRow(
            "Коэффициент для метана (MCF, доля):", self.landfill_mcf_input
        )
        self.landfill_f_input = self._create_line_edit(
            "0.5",
            (0.0, 1.0, 6),
            "Доля метана в образующемся свалочном газе. Стандартное значение - 0.5.",
        )
        params_layout.addRow(
            "Доля CH4 в свалочном газе (F, доля):", self.landfill_f_input
        )
        self.landfill_k_input = self._create_line_edit(
            "0.05",
            (0.0, 1.0, 6),
            "Постоянная реакции разложения (зависит от типа отходов и климата).",
        )
        params_layout.addRow("Постоянная реакции (k, 1/год):", self.landfill_k_input)
        self.landfill_r_input = self._create_line_edit(
            "0.0",
            (0.0, 1e9, 6),
            "Количество метана, собранного за год, в гигаграммах (тыс. тонн).",
        )
        params_layout.addRow("Рекуперированный CH4 (R, Гг/год):", self.landfill_r_input)
        self.landfill_ox_input = self._create_line_edit(
            "0.0",
            (0.0, 1.0, 6),
            "Коэффициент окисления метана. 0.1 для укрытых полигонов, иначе 0.",
        )
        params_layout.addRow(
            "Коэффициент окисления (OX, доля):", self.landfill_ox_input
        )
        layout.addWidget(params_group)

        history_group = QGroupBox(
            "Данные о захоронении отходов (в хронологическом порядке)"
        )
        self.landfill_history_layout = QVBoxLayout(history_group)
        add_btn = QPushButton("Добавить год")
        add_btn.clicked.connect(self._add_landfill_history_row)
        self.landfill_history_layout.addWidget(add_btn)
        layout.addWidget(history_group)
        return scroll_area

    def _add_landfill_history_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        year_label = QLabel(
            f"Год {len(self.landfill_historical_rows) + 1}:"
        )  # ИСПРАВЛЕНО
        mass_input = QLineEdit()
        mass_input.setPlaceholderText("Масса отходов, Гг (тыс. тонн)")
        validator = QDoubleValidator(0.0, 1e9, 6, self)
        validator.setLocale(self.c_locale)
        mass_input.setValidator(validator)
        remove_button = QPushButton("Удалить")
        row_layout.addWidget(year_label)
        row_layout.addWidget(mass_input)
        row_layout.addWidget(remove_button)
        row_data = {"widget": row_widget, "mass_input": mass_input}
        self.landfill_historical_rows.append(row_data)
        self.landfill_history_layout.insertWidget(
            self.landfill_history_layout.count() - 1, row_widget
        )
        remove_button.clicked.connect(
            lambda: self._remove_row(
                row_data, self.landfill_history_layout, self.landfill_historical_rows
            )
        )

    def _remove_row(self, row_data, layout, storage):
        row_widget = row_data["widget"]
        layout.removeWidget(row_widget)
        row_widget.deleteLater()
        storage.remove(row_data)
        if storage is self.landfill_historical_rows:
            for i, row in enumerate(storage):
                row["widget"].findChild(QLabel).setText(f"Год {i+1}:")  # ИСПРАВЛЕНО

    def _create_line_edit(self, default_text="", validator_params=None, tooltip=""):
        line_edit = QLineEdit(default_text)
        line_edit.setToolTip(tooltip)
        if validator_params:
            validator = QDoubleValidator(*validator_params, self)
            validator.setLocale(self.c_locale)
            line_edit.setValidator(validator)
        return line_edit

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        try:
            if not self.landfill_historical_rows:
                raise ValueError("Добавьте данные о захоронении хотя бы за один год.")
            doc = self._get_float(self.landfill_doc_input, "DOC")
            doc_f = self._get_float(self.landfill_docf_input, "DOCf")
            mcf = self._get_float(self.landfill_mcf_input, "MCF")
            f = self._get_float(self.landfill_f_input, "F")
            k = self._get_float(self.landfill_k_input, "k")
            R = self._get_float(self.landfill_r_input, "R")
            OX = self._get_float(self.landfill_ox_input, "OX")
            historical_waste = [
                self._get_float(r["mass_input"], f"Масса за Год {i+1}")
                for i, r in enumerate(self.landfill_historical_rows)
            ]

            emissions_list = self.calculator.calculate_landfill_ch4_emissions(
                historical_waste, doc, doc_f, mcf, f, k, R, OX
            )

            result_text = "Результат (выбросы CH4 в тоннах):\n"
            for year, emission in enumerate(emissions_list, 1):
                result_text += f"Год {year}: {emission:.4f}\n"
            self.result_label.setText(result_text)
            logging.info(
                f"Category 20 calculation successful. Final year emission: {emissions_list[-1]}"
            )
        except ValueError as e:
            logging.error(f"Category 20 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 20 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Критическая ошибка", str(e))
            self.result_label.setText(f"Результат: Ошибка - {e}")
