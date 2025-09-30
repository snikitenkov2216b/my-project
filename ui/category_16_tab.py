# ui/category_16_tab.py - Виджет вкладки для расчетов по Категории 16.
# Код обновлен для приема калькулятора, добавления подсказок и логирования.
# Комментарии на русском. Поддержка UTF-8.

import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QStackedWidget,
    QGroupBox,
    QScrollArea,
    QCheckBox,
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_16 import Category16Calculator


class Category16Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 16 "Производство первичного алюминия".
    """

    def __init__(self, calculator: Category16Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        process_layout = QFormLayout()
        self.process_combobox = QComboBox()
        self.process_combobox.addItems(
            [
                "Выбросы ПФУ (CF4, C2F6)",
                "Выбросы CO2 (Электролизеры Содерберга)",
                "Выбросы CO2 (Обожженные аноды)",
                "Выбросы CO2 от прокалки кокса",
                "Выбросы CO2 от обжига 'зеленых' анодов",
            ]
        )
        process_layout.addRow("Выберите тип расчета:", self.process_combobox)
        main_layout.addLayout(process_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_pfc_widget())
        self.stacked_widget.addWidget(self._create_soderberg_widget())
        self.stacked_widget.addWidget(self._create_prebaked_anode_widget())
        self.stacked_widget.addWidget(self._create_coke_calcination_widget())
        self.stacked_widget.addWidget(self._create_green_anode_baking_widget())
        main_layout.addWidget(self.stacked_widget)
        self.process_combobox.currentIndexChanged.connect(
            self.stacked_widget.setCurrentIndex
        )

        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(
            self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight
        )
        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_line_edit(
        self, default_text="", validator_params=None, placeholder="", tooltip=""
    ):
        line_edit = QLineEdit(default_text)
        line_edit.setPlaceholderText(placeholder)
        line_edit.setToolTip(tooltip)
        if validator_params:
            validator = QDoubleValidator(*validator_params, self)
            validator.setLocale(self.c_locale)
            line_edit.setValidator(validator)
        return line_edit

    def _create_scrollable_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(widget)
        return scroll, layout

    def _create_pfc_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.pfc_tech_combobox = QComboBox()
        self.pfc_tech_combobox.addItems(
            self.calculator.data_service.get_aluminium_tech_types_16_1()
        )
        layout.addRow("Технология электролизера:", self.pfc_tech_combobox)
        self.pfc_al_production_input = self._create_line_edit(
            "", (0.0, 1e9, 6), tooltip="Годовой объем производства первичного алюминия."
        )
        layout.addRow("Производство алюминия (т/год):", self.pfc_al_production_input)
        self.pfc_aef_input = self._create_line_edit(
            "",
            (0.0, 1e9, 6),
            tooltip="Среднее количество анодных эффектов на одну ванну в сутки.",
        )
        layout.addRow("Частота анодных эффектов (шт./ванно-сутки):", self.pfc_aef_input)
        self.pfc_aed_input = self._create_line_edit(
            "",
            (0.0, 1e9, 6),
            tooltip="Средняя продолжительность одного анодного эффекта в минутах.",
        )
        layout.addRow("Длительность анодных эффектов (мин/шт.):", self.pfc_aed_input)
        return widget

    def _create_soderberg_widget(self):
        scroll, layout = self._create_scrollable_area()
        base_group = QGroupBox("Основные параметры")
        base_layout = QFormLayout(base_group)
        self.soderberg_paste_input = self._create_line_edit("", (0.0, 1e9, 6))
        base_layout.addRow("Расход анодной массы (т/т Al):", self.soderberg_paste_input)
        self.soderberg_h_input = self._create_line_edit("", (0.0, 100.0, 4))
        base_layout.addRow("Содержание H в массе (%):", self.soderberg_h_input)
        self.soderberg_s_input = self._create_line_edit("", (0.0, 100.0, 4))
        base_layout.addRow("Содержание S в массе (%):", self.soderberg_s_input)
        self.soderberg_z_input = self._create_line_edit("", (0.0, 100.0, 4))
        base_layout.addRow("Содержание золы (Z) в массе (%):", self.soderberg_z_input)
        layout.addWidget(base_group)
        return scroll

    def _create_prebaked_anode_widget(self):
        scroll, layout = self._create_scrollable_area()
        base_group = QGroupBox("Основные параметры")
        base_layout = QFormLayout(base_group)
        self.prebaked_anode_input = self._create_line_edit("", (0.0, 1e9, 6))
        base_layout.addRow(
            "Расход обожженных анодов (т/т Al):", self.prebaked_anode_input
        )
        self.prebaked_s_input = self._create_line_edit("", (0.0, 100.0, 4))
        base_layout.addRow("Содержание S в аноде (%):", self.prebaked_s_input)
        self.prebaked_z_input = self._create_line_edit("", (0.0, 100.0, 4))
        base_layout.addRow("Содержание золы (Z) в аноде (%):", self.prebaked_z_input)
        layout.addWidget(base_group)
        return scroll

    def _create_coke_calcination_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.coke_calc_consumption_input = self._create_line_edit("", (0.0, 1e9, 6))
        layout.addRow("Расход сырого кокса (т):", self.coke_calc_consumption_input)
        self.coke_calc_loss_input = self._create_line_edit("", (0.0, 100.0, 4))
        layout.addRow("Угар кокса при прокалке (%):", self.coke_calc_loss_input)
        self.coke_calc_carbon_input = self._create_line_edit("", (0.0, 100.0, 4))
        layout.addRow("Содержание углерода в коксе (%):", self.coke_calc_carbon_input)
        return widget

    def _create_green_anode_baking_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.green_anode_prod_input = self._create_line_edit("", (0.0, 1e9, 6))
        layout.addRow("Производство 'зеленых' анодов (т):", self.green_anode_prod_input)
        return widget

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        try:
            current_process = self.process_combobox.currentIndex()
            result_text = ""
            if current_process == 0:
                tech = self.pfc_tech_combobox.currentText()
                prod = self._get_float(self.pfc_al_production_input, "Производство Al")
                aef = self._get_float(self.pfc_aef_input, "Частота анодных эффектов")
                aed = self._get_float(
                    self.pfc_aed_input, "Длительность анодных эффектов"
                )
                pfc_emissions = self.calculator.calculate_pfc_emissions(
                    tech, prod, aef, aed
                )
                result_text = f"Результат: {pfc_emissions['cf4']:.4f} т CF4, {pfc_emissions['c2f6']:.4f} т C2F6"
            elif current_process == 1:
                paste = self._get_float(
                    self.soderberg_paste_input, "Расход анодной массы"
                )
                h = self._get_float(self.soderberg_h_input, "Содержание H")
                s = self._get_float(self.soderberg_s_input, "Содержание S")
                z = self._get_float(self.soderberg_z_input, "Содержание золы")
                co2_emissions = self.calculator.calculate_soderberg_co2_emissions(
                    paste, h, s, z
                )
                result_text = f"Результат: {co2_emissions:.4f} т CO2 / т Al"
            elif current_process == 2:
                anode_cons = self._get_float(self.prebaked_anode_input, "Расход анодов")
                s = self._get_float(self.prebaked_s_input, "Содержание S")
                z = self._get_float(self.prebaked_z_input, "Содержание золы")
                co2_emissions = self.calculator.calculate_prebaked_anode_co2_emissions(
                    anode_cons, s, z
                )
                result_text = f"Результат: {co2_emissions:.4f} т CO2 / т Al"
            elif current_process == 3:
                coke_cons = self._get_float(
                    self.coke_calc_consumption_input, "Расход кокса"
                )
                loss = self._get_float(self.coke_calc_loss_input, "Угар кокса")
                carbon = self._get_float(self.coke_calc_carbon_input, "Содержание C")
                co2_emissions = self.calculator.calculate_coke_calcination_co2(
                    coke_cons, loss, carbon
                )
                result_text = f"Результат: {co2_emissions:.4f} тонн CO2"
            elif current_process == 4:
                anode_prod = self._get_float(
                    self.green_anode_prod_input, "Производство анодов"
                )
                co2_emissions = self.calculator.calculate_green_anode_baking_co2(
                    anode_prod
                )
                result_text = f"Результат: {co2_emissions:.4f} тонн CO2"

            self.result_label.setText(result_text)
            logging.info(f"Category 16 calculation successful: {result_text}")
        except ValueError as e:
            logging.error(f"Category 16 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 16 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Критическая ошибка", str(e))
            self.result_label.setText("Результат: Ошибка")
