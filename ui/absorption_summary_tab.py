# ui/absorption_summary_tab.py
"""
Сводная вкладка для расчетов поглощения ПГ.
"""
import logging
import math
from typing import List, Dict, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QGroupBox,
    QTextEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QSpinBox, QDoubleSpinBox, QMessageBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt, QLocale

from data_models_extended import ExtendedDataService
from calculations.calculator_factory_extended import ExtendedCalculatorFactory

from ui.tab_data_mixin import TabDataMixin
from ui.absorption_utils import create_line_edit, get_float, handle_error


class AbsorptionSummaryTab(TabDataMixin, QWidget):
    """Вкладка для сводного расчета поглощения."""
    def __init__(self, factory: ExtendedCalculatorFactory, absorption_tabs: QTabWidget = None, parent=None):
        super().__init__(parent)
        self.factory = factory
        self.absorption_tabs = absorption_tabs
        self._init_ui()
        logging.info("AbsorptionSummaryTab initialized.")

    def _init_ui(self):
        main_layout = QVBoxLayout(self); main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        label = QLabel("Сводный расчет поглощения"); label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(label)
        self.summary_button = QPushButton("Собрать данные и рассчитать итог"); self.summary_button.clicked.connect(self._calculate_summary)
        main_layout.addWidget(self.summary_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.result_text = QTextEdit("Нажмите кнопку для расчета сводного поглощения...")
        self.result_text.setReadOnly(True)
        main_layout.addWidget(self.result_text)

    def _calculate_summary(self):
        try:
            logging.info("Calculating absorption summary...")
            total_absorption_c = 0.0
            total_emission_co2 = 0.0
            total_emission_ch4 = 0.0
            total_emission_n2o = 0.0
            all_details = ""

            # --- Шаг 1: Сбор данных из других вкладок ---
            if self.absorption_tabs is not None:
                tab_count = self.absorption_tabs.count()
                logging.info(f"Collecting data from {tab_count} absorption tabs...")

                for i in range(tab_count):
                    tab_widget = self.absorption_tabs.widget(i)
                    tab_title = self.absorption_tabs.tabText(i)

                    # Пропускаем саму сводную вкладку
                    if isinstance(tab_widget, AbsorptionSummaryTab):
                        continue

                    # Пробуем получить данные из вкладки
                    if hasattr(tab_widget, 'get_summary_data'):
                        try:
                            data = tab_widget.get_summary_data()
                            total_absorption_c += data.get('absorption_c', 0.0)
                            total_emission_co2 += data.get('emission_co2', 0.0)
                            total_emission_ch4 += data.get('emission_ch4', 0.0)
                            total_emission_n2o += data.get('emission_n2o', 0.0)
                            all_details += data.get('details', '')
                            logging.info(f"Collected data from {tab_title}: absorption_c={data.get('absorption_c', 0):.2f}")
                        except Exception as e:
                            logging.warning(f"Failed to collect data from {tab_title}: {e}")
                            all_details += f"{tab_title}: Ошибка сбора данных\n"
                    else:
                        logging.warning(f"Tab {tab_title} does not have get_summary_data() method")
                        all_details += f"{tab_title}: Метод get_summary_data() не реализован\n"
            else:
                logging.warning("absorption_tabs reference is None - using dummy data")
                QMessageBox.warning(self, "Внимание", "Не удалось получить доступ к вкладкам поглощения.\nИспользуются примерные данные.")
                total_absorption_c = 150.0
                total_emission_co2 = 10.0
                total_emission_ch4 = 0.5
                total_emission_n2o = 0.1
            # --- Шаг 2: Расчет итогов ---
            total_absorption_co2_eq = total_absorption_c * (-44/12)
            gwp_ch4 = 28; gwp_n2o = 265
            total_emission_co2_eq_from_ch4_n2o = (total_emission_ch4 * gwp_ch4) + (total_emission_n2o * gwp_n2o)
            total_emissions_co2_eq = total_emission_co2 + total_emission_co2_eq_from_ch4_n2o
            net_absorption_co2_eq = total_absorption_co2_eq + total_emissions_co2_eq # Поглощение < 0, Выброс > 0
            # --- Шаг 3: Отображение результата ---
            result = f"═══════════════════════════════════════════════════════\n"
            result += f"СВОДНЫЙ РАСЧЕТ ПОГЛОЩЕНИЯ ПАРНИКОВЫХ ГАЗОВ\n"
            result += f"═══════════════════════════════════════════════════════\n\n"

            result += f"📊 ПОГЛОЩЕНИЕ УГЛЕРОДА:\n"
            result += f"  Общее поглощение (ΔC): {total_absorption_c:.4f} т C/год\n"
            result += f"  → Эквивалент CO2: {total_absorption_co2_eq:.4f} т CO2-экв/год\n\n"

            result += f"📤 ВЫБРОСЫ ОТ ИСТОЧНИКОВ В СЕКТОРЕ:\n"
            result += f"  • Прямые выбросы CO2: {total_emission_co2:.4f} т CO2/год\n"
            result += f"  • Выбросы CH4: {total_emission_ch4:.6f} т CH4/год\n"
            result += f"    → CO2-экв: {total_emission_ch4 * gwp_ch4:.4f} т CO2-экв/год (GWP={gwp_ch4})\n"
            result += f"  • Выбросы N2O: {total_emission_n2o:.6f} т N2O/год\n"
            result += f"    → CO2-экв: {total_emission_n2o * gwp_n2o:.4f} т CO2-экв/год (GWP={gwp_n2o})\n"
            result += f"  ───────────────────────────────────────────────────\n"
            result += f"  ИТОГО выбросы: {total_emissions_co2_eq:.4f} т CO2-экв/год\n\n"

            result += f"🌍 ИТОГОВЫЙ БАЛАНС:\n"
            if net_absorption_co2_eq < 0:
                result += f"  ✅ ЧИСТОЕ ПОГЛОЩЕНИЕ: {abs(net_absorption_co2_eq):.4f} т CO2-экв/год\n"
            elif net_absorption_co2_eq > 0:
                result += f"  ⚠️ ЧИСТЫЙ ВЫБРОС: {net_absorption_co2_eq:.4f} т CO2-экв/год\n"
            else:
                result += f"  ⚖️ БАЛАНС: 0.0000 т CO2-экв/год (нейтральный)\n"

            result += f"\n───────────────────────────────────────────────────────\n"
            result += f"📋 ДЕТАЛИ ПО КАТЕГОРИЯМ:\n"
            result += f"───────────────────────────────────────────────────────\n"
            result += all_details if all_details else "  (Нет данных)\n"

            self._append_result(result)
            logging.info(f"AbsorptionSummaryTab: Summary calculated - Net={net_absorption_co2_eq:.4f} t CO2eq/year (Absorption={total_absorption_c:.2f} t C)")
        except Exception as e:
            logging.error(f"Error calculating summary: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при расчете сводки:\n{str(e)}")
