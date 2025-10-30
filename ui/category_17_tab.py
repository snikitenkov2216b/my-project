# ui/category_17_tab.py - Виджет вкладки для расчетов по Категории 17.
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
    QHBoxLayout,
    QGroupBox,
    QScrollArea,
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.category_17 import Category17Calculator
from ui.tab_data_mixin import TabDataMixin



class Category17Tab(TabDataMixin, QWidget):
    """
    Класс виджета-вкладки для Категории 17 "Прочие промышленные процессы".
    """

    def __init__(self, calculator: Category17Calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        (
            self.fuel_use_fuels,
            self.fuel_use_products,
            self.reductants,
            self.carbonates,
        ) = ([], [], [], [])
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        method_layout = QFormLayout()
        self.method_combobox = QComboBox()
        self.method_combobox.addItems(
            [
                "Неэнергетическое использование топлива (Формула 17.1)",
                "Использование восстановителей (Формула 17.2)",
                "Использование карбонатов (Формула 17.3)",
            ]
        )
        method_layout.addRow("Выберите тип процесса:", self.method_combobox)
        main_layout.addLayout(method_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_fuel_use_widget())
        self.stacked_widget.addWidget(self._create_reductants_widget())
        self.stacked_widget.addWidget(self._create_carbonates_widget())
        main_layout.addWidget(self.stacked_widget)
        self.method_combobox.currentIndexChanged.connect(
            self.stacked_widget.setCurrentIndex
        )

        self.calculate_button = QPushButton("Рассчитать выбросы CO2")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(
            self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight
        )
        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_scrollable_widget(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(widget)
        return scroll_area, layout

    def _create_fuel_use_widget(self):
        scroll_area, layout = self._create_scrollable_widget()
        fuels_group = QGroupBox("Использованное топливо")
        self.fuel_use_fuels_layout = QVBoxLayout(fuels_group)
        add_fuel_btn = QPushButton("Добавить топливо")
        add_fuel_btn.clicked.connect(self._add_fuel_use_fuel_row)
        self.fuel_use_fuels_layout.addWidget(add_fuel_btn)
        layout.addWidget(fuels_group)
        products_group = QGroupBox("Продукция, в которой связан углерод")
        self.fuel_use_products_layout = QVBoxLayout(products_group)
        add_product_btn = QPushButton("Добавить продукцию")
        add_product_btn.clicked.connect(self._add_fuel_use_product_row)
        self.fuel_use_products_layout.addWidget(add_product_btn)
        layout.addWidget(products_group)
        return scroll_area

    def _create_reductants_widget(self):
        scroll_area, layout = self._create_scrollable_widget()
        group = QGroupBox("Использованные восстановители")
        self.reductants_layout = QVBoxLayout(group)
        add_btn = QPushButton("Добавить восстановитель")
        add_btn.clicked.connect(self._add_reductant_row)
        self.reductants_layout.addWidget(add_btn)
        layout.addWidget(group)
        return scroll_area

    def _create_carbonates_widget(self):
        scroll_area, layout = self._create_scrollable_widget()
        group = QGroupBox("Использованные карбонаты")
        self.carbonates_layout = QVBoxLayout(group)
        add_btn = QPushButton("Добавить карбонат")
        add_btn.clicked.connect(self._add_carbonate_row)
        self.carbonates_layout.addWidget(add_btn)
        layout.addWidget(group)
        return scroll_area

    def _add_fuel_use_fuel_row(self):
        self._create_dynamic_row(
            self.fuel_use_fuels,
            self.fuel_use_fuels_layout,
            self.calculator.data_service.get_fuels_table_1_1(),
            [("consumption", "Расход", (0.0, 1e9, 6))],
        )

    def _add_fuel_use_product_row(self):
        self._create_dynamic_row(
            self.fuel_use_products,
            self.fuel_use_products_layout,
            self.calculator.data_service.get_fuels_table_1_1(),
            [("production", "Производство, т", (0.0, 1e9, 6))],
        )

    def _add_reductant_row(self):
        self._create_dynamic_row(
            self.reductants,
            self.reductants_layout,
            self.calculator.data_service.get_fuels_table_1_1(),
            [("consumption", "Расход, т", (0.0, 1e9, 6))],
        )

    def _add_carbonate_row(self):
        self._create_dynamic_row(
            self.carbonates,
            self.carbonates_layout,
            self.calculator.data_service.get_carbonate_formulas_table_6_1(),
            [("mass", "Масса, т", (0.0, 1e9, 6))],
        )

    def _create_dynamic_row(self, storage, layout, items, fields):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_data = {"widget": row_widget}
        combo = QComboBox()
        combo.addItems(items)
        row_layout.addWidget(combo)
        row_data["combo"] = combo
        for key, placeholder, params in fields:
            editor = QLineEdit(placeholderText=placeholder)
            validator = QDoubleValidator(*params, self)
            validator.setLocale(self.c_locale)
            editor.setValidator(validator)
            row_layout.addWidget(editor)
            row_data[key] = editor
        remove_button = QPushButton("Удалить")
        row_layout.addWidget(remove_button)
        storage.append(row_data)
        layout.insertWidget(layout.count() - 1, row_widget)
        remove_button.clicked.connect(
            lambda: self._remove_row(row_data, layout, storage)
        )

    def _remove_row(self, row_data, layout, storage):
        row_data["widget"].deleteLater()
        layout.removeWidget(row_data["widget"])
        storage.remove(row_data)

    def _get_float(self, line_edit, field_name):
        text = line_edit.text().replace(",", ".")
        if not text:
            raise ValueError(f"Поле '{field_name}' не заполнено.")
        return float(text)

    def _perform_calculation(self):
        try:
            method_index = self.method_combobox.currentIndex()
            co2_emissions = 0.0

            def collect_data(storage_list, key_name, list_name):
                return [
                    {
                        "name": r["combo"].currentText(),
                        key_name: self._get_float(
                            r[key_name], f"{list_name} для '{r['combo'].currentText()}'"
                        ),
                    }
                    for r in storage_list
                ]

            if method_index == 0:
                fuels = collect_data(self.fuel_use_fuels, "consumption", "Расход")
                products = collect_data(
                    self.fuel_use_products, "production", "Производство"
                )
                if not fuels:
                    raise ValueError("Добавьте хотя бы один вид топлива.")
                    co2_emissions = self.calculator.calculate_from_fuel_use(
                        fuels, products
                    )
            elif method_index == 1:
                reductants = collect_data(self.reductants, "consumption", "Расход")
                if not reductants:
                    raise ValueError("Добавьте хотя бы один восстановитель.")
                    co2_emissions = self.calculator.calculate_from_reductants(
                        reductants
                    )
            elif method_index == 2:
                carbonates = collect_data(self.carbonates, "mass", "Масса")
                if not carbonates:
                    raise ValueError("Добавьте хотя бы один карбонат.")
                    co2_emissions = self.calculator.calculate_from_carbonates(
                        carbonates
                    )

            self.result_label.setText(f"Результат: {co2_emissions:.4f} тонн CO2")
            logging.info(f"Category 17 calculation successful: CO2={co2_emissions}")
        except ValueError as e:
            logging.error(f"Category 17 Calculation - ValueError: {e}")
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            logging.critical(
                f"Category 17 Calculation - Unexpected error: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Критическая ошибка", str(e))
            self.result_label.setText("Результат: Ошибка")
