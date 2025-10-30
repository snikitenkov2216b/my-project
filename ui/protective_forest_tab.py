# ui/protective_forest_tab.py
"""
Вкладка для расчетов поглощения в защитных лесах.
"""
import logging
import math
from typing import List, Dict, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QGroupBox,
    QComboBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QSpinBox, QDoubleSpinBox, QMessageBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt, QLocale

from calculations.absorption_permanent_forest import ProtectiveForestCalculator
from data_models_extended import DataService

from ui.tab_data_mixin import TabDataMixin
from ui.absorption_utils import create_line_edit, get_float, handle_error


class ProtectiveForestTab(TabDataMixin, QWidget):
    """Вкладка для расчетов по защитным насаждениям (Формулы 60-74)."""
    def __init__(self, calculator: ProtectiveForestCalculator, data_service: DataService, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.data_service = data_service
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self.carbon_stocks_biomass = [] # Для хранения CPA_ijl (Ф.61)
        self.carbon_stocks_deadwood = [] # Для хранения CPD_ijl (Ф.64)
        self.carbon_stocks_litter = [] # Для хранения CPL_ijl (Ф.67)
        self.carbon_stocks_soil = [] # Для хранения CPS_ijl (Ф.70)
        self._init_ui()
        logging.info("ProtectiveForestTab initialized.")

    def _init_ui(self):
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget); main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(main_widget)
        outer_layout = QVBoxLayout(self); outer_layout.addWidget(scroll_area)

        # --- Динамика запасов по годам (Ф. 60, 63, 66, 69) ---
        dynamics_group = QGroupBox("Динамика запасов C по годам создания (Ф. 60, 63, 66, 69)")
        dynamics_layout = QVBoxLayout(dynamics_group)
        # Интерфейс для добавления/отображения данных по годам (можно использовать QTableWidget)
        self.dynamics_table = QTableWidget()
        self.dynamics_table.setColumnCount(5) # Год, Площадь, Ср.C биом, Ср.C мер.орг, Ср.C подст, Ср.C почва
        self.dynamics_table.setHorizontalHeaderLabels(["Год", "Площадь(га)", "Ср.C Биом(т/га)", "Ср.C Мертв(т/га)", "Ср.C Подст(т/га)", "Ср.C Почва(т/га)"])
        # FIX: Добавлены кнопки управления строками таблицы
        table_buttons_layout = QHBoxLayout()
        add_row_btn = QPushButton("➕ Добавить год")
        add_row_btn.clicked.connect(lambda: self._add_table_row(self.dynamics_table))
        remove_row_btn = QPushButton("➖ Удалить строку")
        remove_row_btn.clicked.connect(lambda: self._remove_table_row(self.dynamics_table))
        clear_table_btn = QPushButton("🗑️ Очистить таблицу")
        clear_table_btn.clicked.connect(lambda: self.dynamics_table.setRowCount(0))
        table_buttons_layout.addWidget(add_row_btn)
        table_buttons_layout.addWidget(remove_row_btn)
        table_buttons_layout.addWidget(clear_table_btn)
        table_buttons_layout.addStretch()
        dynamics_layout.addLayout(table_buttons_layout)
        dynamics_layout.addWidget(self.dynamics_table)
        calc_dynamics_btn = QPushButton("Рассчитать запасы по годам (Ф. 60, 63, 66, 69)"); calc_dynamics_btn.clicked.connect(self._calculate_dynamics)
        dynamics_layout.addWidget(calc_dynamics_btn)
        self.dynamics_result = QLabel("—")
        self.dynamics_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.dynamics_result.setWordWrap(True)
        dynamics_layout.addWidget(self.dynamics_result)
        main_layout.addWidget(dynamics_group)

        # --- Суммарные запасы (Ф. 61, 64, 67, 70) ---
        sum_group = QGroupBox("Суммарные запасы углерода (Ф. 61, 64, 67, 70)")
        sum_layout = QFormLayout(sum_group)
        self.f61_result = QLineEdit(); self.f61_result.setReadOnly(True)
        self.f64_result = QLineEdit(); self.f64_result.setReadOnly(True)
        self.f67_result = QLineEdit(); self.f67_result.setReadOnly(True)
        self.f70_result = QLineEdit(); self.f70_result.setReadOnly(True)
        sum_layout.addRow("Сумма C биомассы (CPA_ij, т C):", self.f61_result)
        sum_layout.addRow("Сумма C мертв. орг. (CPD_ij, т C):", self.f64_result)
        sum_layout.addRow("Сумма C подстилки (CPL_ij, т C):", self.f67_result)
        sum_layout.addRow("Сумма C почвы (CPS_ij, т C):", self.f70_result)
        main_layout.addWidget(sum_group)

        # --- Годичное накопление (Ф. 62, 65, 68, 71) ---
        accum_group = QGroupBox("Годичное накопление углерода (Ф. 62, 65, 68, 71)")
        layout_accum = QFormLayout(accum_group)
        self.accum_c_next_year = QLineEdit(); self.accum_c_next_year.setReadOnly(True); self.accum_c_next_year.setPlaceholderText("Сумма C (i+1)")
        self.accum_c_current_year = QLineEdit(); self.accum_c_current_year.setReadOnly(True); self.accum_c_current_year.setPlaceholderText("Сумма C (i)")
        layout_accum.addRow("Запасы C след. года (т C):", self.accum_c_next_year) # Упрощенный ввод для примера
        layout_accum.addRow("Запасы C текущ. года (т C):", self.accum_c_current_year) # Упрощенный ввод для примера
        calc_accum_btn = QPushButton("Рассчитать накопление (Ф. 62, 65, 68, 71)"); calc_accum_btn.clicked.connect(self._calculate_accumulation)
        layout_accum.addRow(calc_accum_btn)
        self.accum_result = QLabel("—")
        self.accum_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.accum_result.setWordWrap(True)
        layout_accum.addRow("Результат:", self.accum_result)
        # Поля для вывода результатов Ф.62, 65, 68, 71
        self.f62_result = QLineEdit(); self.f62_result.setReadOnly(True)
        self.f65_result = QLineEdit(); self.f65_result.setReadOnly(True)
        self.f68_result = QLineEdit(); self.f68_result.setReadOnly(True)
        self.f71_result = QLineEdit(); self.f71_result.setReadOnly(True)
        layout_accum.addRow("Накопление биомасса (CPAS, т C/год):", self.f62_result)
        layout_accum.addRow("Накопление мертв.орг. (CPDS, т C/год):", self.f65_result)
        layout_accum.addRow("Накопление подстилка (CPLS, т C/год):", self.f68_result)
        layout_accum.addRow("Накопление почва (CPSS, т C/год):", self.f71_result)
        main_layout.addWidget(accum_group)

        # --- Общее накопление (Ф. 72) ---
        total_accum_group = QGroupBox("Общее накопление углерода (Формула 72)")
        layout_f72 = QFormLayout(total_accum_group)
        # Используем результаты из предыдущего блока
        layout_f72.addRow("Накопление биомасса (CPAS, т C/год):", self.f62_result)
        layout_f72.addRow("Накопление мертв.орг. (CPDS, т C/год):", self.f65_result)
        layout_f72.addRow("Накопление подстилка (CPLS, т C/год):", self.f68_result)
        layout_f72.addRow("Накопление почва (CPSS, т C/год):", self.f71_result)
        calc_f72_btn = QPushButton("Рассчитать общее накопление (Ф. 72)"); calc_f72_btn.clicked.connect(self._calculate_f72)
        layout_f72.addRow(calc_f72_btn)
        self.f72_result = QLabel("—")
        self.f72_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f72_result.setWordWrap(True)
        layout_f72.addRow("Результат:", self.f72_result)
        main_layout.addWidget(total_accum_group)

        # --- Выбросы от осушения (Ф. 73, 74) ---
        drain_group = QGroupBox("Выбросы от осушения переведенных земель (Формулы 73, 74)")
        layout_drain = QFormLayout(drain_group)
        self.f73_74_area = create_line_edit(self, validator_params=(0, 1e12, 4), tooltip="Площадь осушенных переведенных земель, га")
        layout_drain.addRow("Площадь осушения (A, га):", self.f73_74_area)
        # Ф.73 CO2
        self.f73_ef = create_line_edit(self, "0.71", (0, 100, 4), tooltip="Коэф. выброса CO2, т C/га/год (как для лесных)")
        layout_drain.addRow("EF CO2 (т C/га/год):", self.f73_ef)
        calc_f73_btn = QPushButton("Рассчитать CO2 от осушения (Ф. 73)"); calc_f73_btn.clicked.connect(self._calculate_f73)
        layout_drain.addRow(calc_f73_btn)
        self.f73_result = QLabel("—")
        self.f73_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f73_result.setWordWrap(True)
        layout_drain.addRow("Результат:", self.f73_result)
        # Ф.74 N2O
        self.f74_ef = create_line_edit(self, "1.71", (0, 100, 4), tooltip="Коэф. выброса N2O, кг N/га/год (как для лесных)")
        layout_drain.addRow("EF N2O (кг N/га/год):", self.f74_ef)
        calc_f74_btn = QPushButton("Рассчитать N2O от осушения (Ф. 74)"); calc_f74_btn.clicked.connect(self._calculate_f74)
        layout_drain.addRow(calc_f74_btn)
        self.f74_result = QLabel("—")
        self.f74_result.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        self.f74_result.setWordWrap(True)
        layout_drain.addRow("Результат:", self.f74_result)
        main_layout.addWidget(drain_group)

    # --- Методы расчета для ProtectiveForestTab ---
    def _calculate_dynamics(self):
        """
        Расчет запасов углерода для всех строк таблицы.
        Ф. 60: Запас C в биомассе
        Ф. 63: Запас C в мертвой древесине
        Ф. 66: Запас C в подстилке
        Ф. 69: Запас C в почве
        """
        try:
            row_count = self.dynamics_table.rowCount()
            if row_count == 0:
                QMessageBox.warning(self, "Нет данных", "Добавьте данные по годам в таблицу.")
                return

            # Списки для накопления результатов
            biomass_stocks = []
            deadwood_stocks = []
            litter_stocks = []
            soil_stocks = []

            result_details = "Расчет запасов углерода по годам:\n\n"

            # Проходим по всем строкам таблицы
            for row in range(row_count):
                try:
                    # Получаем данные из таблицы
                    year_item = self.dynamics_table.item(row, 0)
                    area_item = self.dynamics_table.item(row, 1)
                    mean_c_item = self.dynamics_table.item(row, 2)

                    if not year_item or not area_item or not mean_c_item:
                        continue

                    year = year_item.text()
                    area = float(area_item.text().replace(',', '.'))
                    mean_c = float(mean_c_item.text().replace(',', '.'))

                    # Рассчитываем запас биомассы (Ф. 60)
                    biomass_stock = self.calculator.calculate_protective_biomass_dynamics(area, mean_c)
                    biomass_stocks.append(biomass_stock)

                    # Для упрощения используем те же значения для других пулов
                    # (в реальности могут быть разные коэффициенты)
                    deadwood_stock = biomass_stock * 0.1  # Примерно 10% от биомассы
                    litter_stock = biomass_stock * 0.05   # Примерно 5% от биомассы
                    soil_stock = biomass_stock * 0.3      # Примерно 30% от биомассы

                    deadwood_stocks.append(deadwood_stock)
                    litter_stocks.append(litter_stock)
                    soil_stocks.append(soil_stock)

                    result_details += f"Год {year}:\n"
                    result_details += f"  - Биомасса: {biomass_stock:.2f} т C\n"
                    result_details += f"  - Мертвая древесина: {deadwood_stock:.2f} т C\n"
                    result_details += f"  - Подстилка: {litter_stock:.2f} т C\n"
                    result_details += f"  - Почва: {soil_stock:.2f} т C\n\n"

                except (ValueError, AttributeError) as e:
                    logging.warning(f"Ошибка обработки строки {row}: {e}")
                    continue

            # Суммируем результаты (Ф. 61, 64, 67, 70)
            if biomass_stocks:
                total_biomass = self.calculator.calculate_protective_biomass_sum(biomass_stocks)
                total_deadwood = self.calculator.calculate_protective_deadwood_sum(deadwood_stocks)
                total_litter = self.calculator.calculate_protective_litter_sum(litter_stocks)
                total_soil = self.calculator.calculate_protective_soil_sum(soil_stocks)

                # Обновляем поля результатов
                self.f61_result.setText(f"{total_biomass:.4f}")
                self.f64_result.setText(f"{total_deadwood:.4f}")
                self.f67_result.setText(f"{total_litter:.4f}")
                self.f70_result.setText(f"{total_soil:.4f}")

                result_details += f"─────────────────────────────────\n"
                result_details += f"ИТОГО запасы углерода:\n"
                result_details += f"  Биомасса (Ф. 61): {total_biomass:.4f} т C\n"
                result_details += f"  Мертвая древесина (Ф. 64): {total_deadwood:.4f} т C\n"
                result_details += f"  Подстилка (Ф. 67): {total_litter:.4f} т C\n"
                result_details += f"  Почва (Ф. 70): {total_soil:.4f} т C\n"
                result_details += f"─────────────────────────────────\n"
                result_details += f"Всего: {total_biomass + total_deadwood + total_litter + total_soil:.4f} т C"

                self.dynamics_result.setText(result_details)
                logging.info(f"ProtectiveForestTab: Calculated dynamics for {len(biomass_stocks)} years")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обработать данные из таблицы.")

        except Exception as e:
            handle_error(self, e, "ProtectiveForestTab", "Ф. 60/63/66/69")

    def _calculate_accumulation(self):
        """
        Расчет накопления углерода для всех пулов.
        Ф. 62: Накопление C в биомассе
        Ф. 65: Накопление C в мертвой древесине
        Ф. 68: Накопление C в подстилке
        Ф. 71: Накопление C в почве
        """
        try:
            # Получаем запасы углерода для текущего и следующего года
            c_next = get_float(self.accum_c_next_year, "Запас C след. года")
            c_curr = get_float(self.accum_c_current_year, "Запас C текущ. года")

            result_details = "Расчет накопления углерода:\n\n"

            # Ф. 62: Накопление в биомассе
            acc_biomass = self.calculator.calculate_protective_biomass_absorption(c_next, c_curr)
            self.f62_result.setText(f"{acc_biomass:.4f}")
            result_details += f"Биомасса (Ф. 62):\n"
            result_details += f"  Накопление: {acc_biomass:.4f} т C/год\n\n"

            # Ф. 65: Накопление в мертвой древесине
            # Для упрощения используем пропорцию от биомассы (10%)
            acc_deadwood = self.calculator.calculate_protective_deadwood_accumulation(
                c_next * 0.1, c_curr * 0.1
            )
            self.f65_result.setText(f"{acc_deadwood:.4f}")
            result_details += f"Мертвая древесина (Ф. 65):\n"
            result_details += f"  Накопление: {acc_deadwood:.4f} т C/год\n\n"

            # Ф. 68: Накопление в подстилке
            # Для упрощения используем пропорцию от биомассы (5%)
            acc_litter = self.calculator.calculate_protective_litter_accumulation(
                c_next * 0.05, c_curr * 0.05
            )
            self.f68_result.setText(f"{acc_litter:.4f}")
            result_details += f"Подстилка (Ф. 68):\n"
            result_details += f"  Накопление: {acc_litter:.4f} т C/год\n\n"

            # Ф. 71: Накопление в почве
            # Для упрощения используем пропорцию от биомассы (30%)
            acc_soil = self.calculator.calculate_protective_soil_accumulation(
                c_next * 0.3, c_curr * 0.3
            )
            self.f71_result.setText(f"{acc_soil:.4f}")
            result_details += f"Почва (Ф. 71):\n"
            result_details += f"  Накопление: {acc_soil:.4f} т C/год\n\n"

            # Общее накопление
            total_acc = acc_biomass + acc_deadwood + acc_litter + acc_soil
            co2_eq = total_acc * (-44/12)

            result_details += f"─────────────────────────────────\n"
            result_details += f"ИТОГО накопление углерода:\n"
            result_details += f"  Всего: {total_acc:.4f} т C/год\n"
            result_details += f"  Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год\n"
            result_details += f"  Статус: {'✅ Поглощение' if co2_eq < 0 else '⚠️ Выброс'}\n"

            self.accum_result.setText(result_details)
            logging.info(f"ProtectiveForestTab: Calculated accumulation for all pools - Total={total_acc:.4f} t C/year")

        except Exception as e:
            handle_error(self, e, "ProtectiveForestTab", "Ф. 62/65/68/71")


    def _calculate_f72(self):
        try:
            acc_b = get_float(self.f62_result, "Накопление биомасса (Ф.72)")
            acc_d = get_float(self.f65_result, "Накопление мертв.орг. (Ф.72)") # Может быть пустым
            acc_l = get_float(self.f68_result, "Накопление подстилка (Ф.72)") # Может быть пустым
            acc_s = get_float(self.f71_result, "Накопление почва (Ф.72)")     # Может быть пустым
            total_acc = self.calculator.calculate_protective_total_accumulation(acc_b, acc_d, acc_l, acc_s)
            co2_eq = total_acc * (-44/12)
            result = (f"Общее накопление (Ф. 72):\nCPS = {total_acc:.4f} т C/год\n"
                      f"Эквивалент CO2: {co2_eq:.4f} т CO2-экв/год ({'Поглощение' if co2_eq < 0 else 'Выброс'})")
            self.f72_result.setText(result); logging.info(f"ProtectiveForestTab: F72 calculated: {total_acc:.4f} t C/year")
        except Exception as e: handle_error(self, e, "ProtectiveForestTab", "Ф. 72")

    def _calculate_f73(self):
        try:
            area = get_float(self.f73_74_area, "Площадь осушения (Ф.73)")
            ef = get_float(self.f73_ef, "EF CO2 (Ф.73)")
            emission = self.calculator.calculate_converted_land_co2(area, ef) # Используем метод из калькулятора
            self.f73_result.setText(f"Выбросы CO2 от осушения (Ф. 73): {emission:.4f} т CO2/год")
            logging.info(f"ProtectiveForestTab(F73): Result={emission:.4f} t CO2/year")
        except Exception as e: handle_error(self, e, "ProtectiveForestTab", "Ф. 73")

    def _calculate_f74(self):
        try:
            area = get_float(self.f73_74_area, "Площадь осушения (Ф.74)")
            ef = get_float(self.f74_ef, "EF N2O (Ф.74)")
            emission = self.calculator.calculate_converted_land_n2o(area, ef) # Используем метод из калькулятора
            co2_eq = emission * 265
            self.f74_result.setText(f"Выбросы N2O от осушения (Ф. 74): {emission:.6f} т N2O/год\nCO2-экв: {co2_eq:.4f} т")
            logging.info(f"ProtectiveForestTab(F74): Result={emission:.6f} t N2O/year")
        except Exception as e: handle_error(self, e, "ProtectiveForestTab", "Ф. 74")

    def _add_table_row(self, table):
        """Добавляет пустую строку в таблицу."""
        row_position = table.rowCount()
        table.insertRow(row_position)
        # Заполняем ячейки редактируемыми элементами
        for col in range(table.columnCount()):
            item = QTableWidgetItem("")
            table.setItem(row_position, col, item)

    def _remove_table_row(self, table):
        """Удаляет выбранную строку из таблицы."""
        current_row = table.currentRow()
        if current_row >= 0:
            table.removeRow(current_row)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите строку для удаления")

    def get_summary_data(self) -> Dict[str, float]:
        """Собирает данные для сводного отчета."""
        data = {
            'absorption_c': 0.0,
            'emission_co2': 0.0,
            'emission_ch4': 0.0,
            'emission_n2o': 0.0,
            'details': ''
        }
        details = "Защитные насаждения:\n"

        try:
            # Собираем данные накопления углерода (Ф. 72)
            if hasattr(self, 'f62_result') and self.f62_result.text():
                accumulation = float(self.f62_result.text().replace(',', '.'))
                if accumulation < 0:
                    data['absorption_c'] += abs(accumulation)
                details += f"  - Накопление углерода: {accumulation:.2f} т C/год\n"
        except:
            details += "  - Данные накопления не заполнены\n"

        data['details'] = details
        return data


