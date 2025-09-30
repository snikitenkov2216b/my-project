# ui/dashboard_tab.py - Виджет вкладки для дашборда.
# Отображает сводную информацию по выбросам со всех категорий.
# Комментарии на русском. Поддержка UTF-8.

import logging
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QScrollArea,
    QGridLayout, QTextEdit
)
from PyQt6.QtCore import Qt

class DashboardTab(QWidget):
    """
    Класс виджета-вкладки для главной панели (Dashboard).
    Собирает и суммирует результаты расчетов со всех остальных вкладок.
    """
    def __init__(self, tabs_widget, parent=None):
        super().__init__(parent)
        self.tabs_widget = tabs_widget
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Кнопка обновления ---
        self.refresh_button = QPushButton("Обновить сводку")
        self.refresh_button.clicked.connect(self.refresh_summary)
        main_layout.addWidget(self.refresh_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Группа для итоговых суммарных выбросов ---
        total_group = QGroupBox("Суммарные выбросы")
        self.total_layout = QGridLayout(total_group)
        main_layout.addWidget(total_group)
        
        # --- Область для отображения детальных результатов ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        results_widget = QWidget()
        self.results_layout = QVBoxLayout(results_widget)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(results_widget)
        main_layout.addWidget(scroll_area)

        # Создаем метки для итогов, они будут заполняться при обновлении
        self.summary_labels = {
            "CO2": QLabel("..."),
            "CH4": QLabel("..."),
            "N2O": QLabel("..."),
            "ПФУ и др.": QLabel("..."), # Для CF4, C2F6, SF6, CHF3
            "CO2-экв": QLabel("...")
        }
        
        row = 0
        for name, label in self.summary_labels.items():
            label.setStyleSheet("font-weight: bold; font-size: 14px;")
            self.total_layout.addWidget(QLabel(f"Всего {name}:"), row, 0)
            self.total_layout.addWidget(label, row, 1)
            row += 1

        self.details_label = QLabel("<b>Детализация по категориям:</b>")
        self.results_layout.addWidget(self.details_label)

    def refresh_summary(self):
        """
        Собирает данные со всех вкладок, суммирует их и обновляет дашборд.
        """
        totals = {
            "CO2": 0.0, "CH4": 0.0, "N2O": 0.0,
            "CF4": 0.0, "C2F6": 0.0, "SF6": 0.0, "CHF3": 0.0
        }
        
        # Очищаем старые детализированные результаты
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        details_html = ""

        # Проходим по всем вкладкам, кроме первой (самого дашборда)
        for i in range(1, self.tabs_widget.count()):
            tab = self.tabs_widget.widget(i)
            tab_name = self.tabs_widget.tabText(i)
            
            if hasattr(tab, 'result_label'):
                try:
                    result_text = ""
                    if isinstance(tab.result_label, QLabel):
                        result_text = tab.result_label.text()
                    elif isinstance(tab.result_label, QTextEdit):
                        result_text = tab.result_label.toPlainText()
                    
                    if "Результат:" in result_text and "Ошибка" not in result_text and "..." not in result_text:
                        current_tab_details = ""
                        
                        # Парсинг результатов из текста метки
                        matches = re.findall(r'([\d\.\,]+)\s*т(?:онн)?\s*(CO2|CH4|N2O|CF4|C2F6|SF6|CHF3)', result_text, re.IGNORECASE)

                        if matches:
                            current_tab_details += f"<b>{tab_name}:</b><br>"
                            for value_str, gas_name in matches:
                                value = float(value_str.replace(',', '.'))
                                gas_upper = gas_name.upper()
                                if gas_upper in totals:
                                    totals[gas_upper] += value
                                    current_tab_details += f"&nbsp;&nbsp;&nbsp;{gas_upper}: {value:.4f} т<br>"
                            details_html += current_tab_details
                except Exception as e:
                    logging.warning(f"Не удалось обработать результат из вкладки '{tab_name}': {e}")

        # Добавляем детализацию в layout
        details_label = QLabel(details_html)
        details_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        details_label.setWordWrap(True)
        self.results_layout.addWidget(details_label)

        # Потенциалы глобального потепления (GWP) за 100 лет (AR5)
        gwp = {"CO2": 1, "CH4": 28, "N2O": 265, "CF4": 7390, "C2F6": 12200, "SF6": 23500, "CHF3": 14800}

        total_others = totals["CF4"] + totals["C2F6"] + totals["SF6"] + totals["CHF3"]
        
        total_co2_eq = (
            totals["CO2"] * gwp["CO2"] +
            totals["CH4"] * gwp["CH4"] +
            totals["N2O"] * gwp["N2O"] +
            total_others * sum(gwp[gas] for gas in ["CF4", "C2F6", "SF6", "CHF3"] if gas in totals) / 4 # Усредненный GWP для ПФУ
        )

        # Обновляем итоговые метки
        self.summary_labels["CO2"].setText(f"{totals['CO2']:.4f} тонн")
        self.summary_labels["CH4"].setText(f"{totals['CH4']:.4f} тонн")
        self.summary_labels["N2O"].setText(f"{totals['N2O']:.4f} тонн")
        self.summary_labels["ПФУ и др."].setText(f"{total_others:.4f} тонн")
        self.summary_labels["CO2-экв"].setText(f"{total_co2_eq:.4f} тонн")