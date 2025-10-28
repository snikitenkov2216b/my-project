# ui/forest_restoration_tab_improved.py
"""
Улучшенная версия вкладки для расчетов лесовосстановления (формулы 1-12).
Использует AbsorptionBaseTab для устранения дублирования кода.
"""
import logging
from PyQt6.QtWidgets import (
    QPushButton, QComboBox, QSpinBox, QTableWidget,
    QTableWidgetItem, QHBoxLayout, QLineEdit, QVBoxLayout,
)
from PyQt6.QtCore import Qt

from ui.absorption_base_tab import AbsorptionBaseTab
from calculations.absorption_forest_restoration import ForestRestorationCalculator


class ForestRestorationTabImproved(AbsorptionBaseTab):
    """
    Улучшенная вкладка для расчетов лесовосстановления (формулы 1-12).

    Использует базовый класс AbsorptionBaseTab для:
    - Единого стиля интерфейса
    - Автоматического добавления единиц измерения
    - Кнопки "Очистить все поля"
    - Улучшенной обработки ошибок
    """

    def __init__(self, calculator: ForestRestorationCalculator, parent=None):
        super().__init__(calculator, parent)
        self._init_ui()
        logging.info("ForestRestorationTabImproved initialized.")

    def _init_ui(self):
        """Инициализация UI."""
        layout = self._create_main_layout()

        # Заголовок
        title_label = self._create_result_area()
        title_label.setText(
            "<h2 style='color: #2e7d32;'>Лесовосстановление (Формулы 1-12)</h2>"
            "<p>Расчеты поглощения парниковых газов при лесовосстановлении</p>"
        )
        layout.addWidget(title_label)

        # === Формула 1: Общее изменение запасов углерода ===
        group1, form1 = self._create_group_box("1. Общее изменение запасов углерода (Формула 1)")

        self.f1_biomass = self._create_line_edit(
            validator_params=(-1e9, 1e9, 4),
            tooltip="Изменение углерода в живой биомассе, т C/год"
        )
        self._add_label_with_units(form1, "ΔC биомасса", "carbon_tonnes_per_year", self.f1_biomass)

        self.f1_deadwood = self._create_line_edit(
            validator_params=(-1e9, 1e9, 4),
            tooltip="Изменение углерода в мертвой древесине, т C/год"
        )
        self._add_label_with_units(form1, "ΔC мертвая древесина", "carbon_tonnes_per_year", self.f1_deadwood)

        self.f1_litter = self._create_line_edit(
            validator_params=(-1e9, 1e9, 4),
            tooltip="Изменение углерода в лесной подстилке, т C/год"
        )
        self._add_label_with_units(form1, "ΔC подстилка", "carbon_tonnes_per_year", self.f1_litter)

        self.f1_soil = self._create_line_edit(
            validator_params=(-1e9, 1e9, 4),
            tooltip="Изменение углерода в почве, т C/год"
        )
        self._add_label_with_units(form1, "ΔC почва", "carbon_tonnes_per_year", self.f1_soil)

        calc_f1_btn = self._create_calculate_button("Рассчитать ΔC общее (Ф. 1)")
        calc_f1_btn.clicked.connect(self._calculate_f1)
        form1.addRow(calc_f1_btn)

        layout.addWidget(group1)

        # === Формула 2: Изменение запасов C в биомассе ===
        group2, form2 = self._create_group_box("2. Изменение запасов C в биомассе (Формула 2)")

        self.f2_c_after = self._create_line_edit(
            validator_params=(0, 1e9, 4),
            tooltip="Запас углерода ПОСЛЕ лесовосстановления"
        )
        self._add_label_with_units(form2, "C после", "carbon_tonnes_per_ha", self.f2_c_after)

        self.f2_c_before = self._create_line_edit(
            validator_params=(0, 1e9, 4),
            tooltip="Запас углерода ДО лесовосстановления"
        )
        self._add_label_with_units(form2, "C до", "carbon_tonnes_per_ha", self.f2_c_before)

        self.f2_area = self._create_line_edit(
            validator_params=(0, 1e12, 4),
            tooltip="Площадь лесовосстановления"
        )
        self._add_label_with_units(form2, "Площадь (A)", "area_hectares", self.f2_area)

        self.f2_period = self._create_line_edit(
            default="5",
            validator_params=(1, 100, 1),
            tooltip="Период между измерениями"
        )
        self._add_label_with_units(form2, "Период (D)", "period_years", self.f2_period)

        calc_f2_btn = self._create_calculate_button("Рассчитать ΔC биомассы (Ф. 2)")
        calc_f2_btn.clicked.connect(self._calculate_f2)
        form2.addRow(calc_f2_btn)

        layout.addWidget(group2)

        # === Формула 3: Биомасса дерева ===
        group3, form3 = self._create_group_box("3. Углерод в биомассе древостоя (Формула 3)")

        self.f3_species = QComboBox()
        species_list = list(self.calculator.ALLOMETRIC_COEFFICIENTS.keys())
        self.f3_species.addItems([s.capitalize() for s in species_list])
        self.f3_species.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 10pt;
            }
        """)
        form3.addRow("Порода дерева:", self.f3_species)

        self.f3_diameter = self._create_line_edit(
            validator_params=(0.1, 1000, 2),
            tooltip="Диаметр ствола на высоте 1.3 м"
        )
        self._add_label_with_units(form3, "Диаметр (d)", "diameter_cm", self.f3_diameter)

        self.f3_height = self._create_line_edit(
            validator_params=(0.1, 100, 2),
            tooltip="Высота дерева"
        )
        self._add_label_with_units(form3, "Высота (h)", "height_m", self.f3_height)

        self.f3_count = QSpinBox()
        self.f3_count.setRange(1, 1000000)
        self.f3_count.setValue(1)
        self.f3_count.setStyleSheet("""
            QSpinBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 10pt;
            }
        """)
        form3.addRow("Количество деревьев:", self.f3_count)

        calc_f3_btn = self._create_calculate_button("Рассчитать C древостоя (Ф. 3)")
        calc_f3_btn.clicked.connect(self._calculate_f3)
        form3.addRow(calc_f3_btn)

        layout.addWidget(group3)

        # === Формула 5: Запас углерода в почве ===
        group5, form5 = self._create_group_box("5. Запас углерода в почве (Формула 5)")

        self.f5_org_percent = self._create_line_edit(
            validator_params=(0, 100, 4),
            tooltip="Содержание органического вещества в почве"
        )
        self._add_label_with_units(form5, "Органическое вещество", "organic_percent", self.f5_org_percent)

        self.f5_depth_cm = self._create_line_edit(
            default="30",
            validator_params=(1, 200, 2),
            tooltip="Глубина отбора проб почвы"
        )
        self._add_label_with_units(form5, "Глубина (H)", "depth_cm", self.f5_depth_cm)

        self.f5_bulk_density = self._create_line_edit(
            validator_params=(0.1, 5, 4),
            tooltip="Объемная масса почвы"
        )
        self._add_label_with_units(form5, "Объемная масса", "bulk_density", self.f5_bulk_density)

        calc_f5_btn = self._create_calculate_button("Рассчитать C почвы (Ф. 5)")
        calc_f5_btn.clicked.connect(self._calculate_f5)
        form5.addRow(calc_f5_btn)

        layout.addWidget(group5)

        # === Формула 6: Выбросы от пожаров ===
        group6, form6 = self._create_group_box("6. Выбросы ПГ от пожаров (Формула 6)")

        self.f6_area = self._create_line_edit(
            validator_params=(0, 1e9, 4),
            tooltip="Площадь, пройденная пожаром"
        )
        self._add_label_with_units(form6, "Площадь (A)", "area_hectares", self.f6_area)

        self.f6_fuel_mass = self._create_line_edit(
            default="121.4",
            validator_params=(0, 1000, 4),
            tooltip="Масса горючего материала на единицу площади"
        )
        self._add_label_with_units(form6, "Масса топлива (M_B)", "biomass_tonnes_per_ha", self.f6_fuel_mass)

        self.f6_comb_factor = self._create_line_edit(
            default="0.43",
            validator_params=(0.01, 1.0, 3),
            tooltip="Коэффициент сгорания (0.43 - верховой, 0.15 - низовой)"
        )
        self._add_label_with_units(form6, "Коэффициент сгорания (C_f)", "combustion_factor", self.f6_comb_factor)

        self.f6_gas_type = QComboBox()
        self.f6_gas_type.addItems(["CO2", "CH4", "N2O"])
        self.f6_gas_type.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 10pt;
            }
        """)
        form6.addRow("Тип парникового газа:", self.f6_gas_type)

        calc_f6_btn = self._create_calculate_button("Рассчитать выбросы от пожара (Ф. 6)")
        calc_f6_btn.clicked.connect(self._calculate_f6)
        form6.addRow(calc_f6_btn)

        layout.addWidget(group6)

        # === Область результатов ===
        result_area = self._create_result_area()
        layout.addWidget(result_area)

        # === Кнопки управления ===
        buttons_layout = self._create_buttons_layout(
            self._create_clear_button()
        )
        layout.addLayout(buttons_layout)

        layout.addStretch()

    # === Обработчики расчетов ===

    def _calculate_f1(self):
        """Формула 1: Суммарное изменение запасов углерода."""
        try:
            biomass = self._get_float(self.f1_biomass, "ΔC биомасса")
            deadwood = self._get_float(self.f1_deadwood, "ΔC мертвая древесина")
            litter = self._get_float(self.f1_litter, "ΔC подстилка")
            soil = self._get_float(self.f1_soil, "ΔC почва")

            result = self.calculator.calculate_carbon_stock_change(
                biomass, deadwood, litter, soil
            )

            self._display_result("Формула 1: Общее изменение запасов углерода", result, "т C/год")

        except Exception as e:
            self._handle_error(e, "Формула 1")

    def _calculate_f2(self):
        """Формула 2: Изменение запасов углерода в биомассе."""
        try:
            c_after = self._get_float(self.f2_c_after, "C после")
            c_before = self._get_float(self.f2_c_before, "C до")
            area = self._get_float(self.f2_area, "Площадь")
            period = self._get_float(self.f2_period, "Период")

            result = self.calculator.calculate_biomass_change(
                c_after, c_before, area, period
            )

            self._display_result("Формула 2: Изменение запасов C в биомассе", result, "т C/год")

        except Exception as e:
            self._handle_error(e, "Формула 2")

    def _calculate_f3(self):
        """Формула 3: Биомасса дерева."""
        try:
            diameter = self._get_float(self.f3_diameter, "Диаметр")
            height = self._get_float(self.f3_height, "Высота")
            species = self.f3_species.currentText().lower()
            count = self.f3_count.value()

            biomass_per_tree = self.calculator.calculate_tree_biomass(
                diameter, height, species, "всего"
            )

            carbon = self.calculator.calculate_carbon_from_biomass(biomass_per_tree)
            total_carbon = carbon * count

            result_text = (
                f"<b>Формула 3: Углерод в биомассе древостоя</b><br>"
                f"<b>Биомасса 1 дерева:</b> {biomass_per_tree:.2f} кг<br>"
                f"<b>Углерод 1 дерева:</b> {carbon:.4f} т C<br>"
                f"<b>Углерод {count} деревьев:</b> "
                f"<span style='font-size: 14pt; color: #1b5e20;'><b>{total_carbon:.4f}</b> т C</span>"
            )
            self.result_text.setText(result_text)

            logging.info(f"Formula 3: Biomass={biomass_per_tree:.2f} kg, Carbon={total_carbon:.4f} т C")

        except Exception as e:
            self._handle_error(e, "Формула 3")

    def _calculate_f5(self):
        """Формула 5: Запас углерода в почве."""
        try:
            org_percent = self._get_float(self.f5_org_percent, "Органическое вещество")
            depth = self._get_float(self.f5_depth_cm, "Глубина")
            bulk_density = self._get_float(self.f5_bulk_density, "Объемная масса")

            result = self.calculator.calculate_soil_carbon(
                org_percent, depth, bulk_density
            )

            self._display_result("Формула 5: Запас углерода в почве", result, "т C/га")

        except Exception as e:
            self._handle_error(e, "Формула 5")

    def _calculate_f6(self):
        """Формула 6: Выбросы ПГ от пожаров."""
        try:
            area = self._get_float(self.f6_area, "Площадь")
            fuel_mass = self._get_float(self.f6_fuel_mass, "Масса топлива")
            comb_factor = self._get_float(self.f6_comb_factor, "Коэффициент сгорания")
            gas_type = self.f6_gas_type.currentText()

            result = self.calculator.calculate_fire_emissions(
                area, fuel_mass, comb_factor, gas_type
            )

            self._display_result(f"Формула 6: Выбросы {gas_type} от пожаров", result, "т")

        except Exception as e:
            self._handle_error(e, "Формула 6")
