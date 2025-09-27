# ui/category_16_tab.py - Виджет вкладки для расчетов по Категории 16.
# Реализует сложный интерфейс для различных процессов производства алюминия.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt

from data_models import DataService
from calculations.category_16 import Category16Calculator

class Category16Tab(QWidget):
    """
    Класс виджета-вкладки для Категории 16 "Производство первичного алюминия".
    """
    def __init__(self, data_service: DataService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.calculator = Category16Calculator(self.data_service)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Выбор типа расчета ---
        self.calc_type_combobox = QComboBox()
        self.calc_type_combobox.addItems([
            "Выбросы перфторуглеродов (ПФУ)",
            "Выбросы CO2 (электролизеры Содерберга)",
            "Выбросы CO2 (электролизеры с обожженными анодами)",
            "Выбросы CO2 (прокалка кокса)",
            "Выбросы CO2 (обжиг 'зеленых' анодов)"
        ])
        main_layout.addWidget(QLabel("Выберите тип расчета:"))
        main_layout.addWidget(self.calc_type_combobox)

        # --- Стек виджетов для разных форм ввода ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_pfc_widget())
        self.stacked_widget.addWidget(self._create_soderberg_widget())
        self.stacked_widget.addWidget(self._create_prebaked_anode_widget())
        self.stacked_widget.addWidget(self._create_coke_calcination_widget())
        self.stacked_widget.addWidget(self._create_green_anode_baking_widget())
        main_layout.addWidget(self.stacked_widget)

        self.calc_type_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)

        # --- Кнопка расчета и область результатов ---
        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_pfc_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.pfc_technology_combobox = QComboBox()
        self.pfc_technology_combobox.addItems([item['technology'] for item in self.data_service.table_16_1])
        layout.addRow("Технология:", self.pfc_technology_combobox)

        self.aluminium_production_input = QLineEdit()
        self.aluminium_production_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        layout.addRow("Выпуск алюминия (т/год):", self.aluminium_production_input)

        self.aef_input = QLineEdit()
        self.aef_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        layout.addRow("Частота анодных эффектов (шт./ванно-сутки):", self.aef_input)

        self.aed_input = QLineEdit()
        self.aed_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        layout.addRow("Продолжительность анодных эффектов (минут/шт.):", self.aed_input)
        
        return widget

    def _create_soderberg_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.soderberg_anode_paste_input = QLineEdit()
        self.soderberg_anode_paste_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        layout.addRow("Расход анодной массы (т/т Ал.):", self.soderberg_anode_paste_input)

        self.soderberg_h_input = QLineEdit("1.4")
        self.soderberg_h_input.setValidator(QDoubleValidator(0.0, 100.0, 4, self))
        layout.addRow("Содержание водорода в массе (%):", self.soderberg_h_input)
        
        self.soderberg_s_input = QLineEdit()
        self.soderberg_s_input.setValidator(QDoubleValidator(0.0, 100.0, 4, self))
        layout.addRow("Содержание серы в массе (%):", self.soderberg_s_input)

        self.soderberg_z_input = QLineEdit()
        self.soderberg_z_input.setValidator(QDoubleValidator(0.0, 100.0, 4, self))
        layout.addRow("Содержание золы в массе (%):", self.soderberg_z_input)

        return widget

    def _create_prebaked_anode_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.prebaked_anode_input = QLineEdit()
        self.prebaked_anode_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        layout.addRow("Расход обожженных анодов нетто (т/т Ал.):", self.prebaked_anode_input)
        
        self.prebaked_s_input = QLineEdit()
        self.prebaked_s_input.setValidator(QDoubleValidator(0.0, 100.0, 4, self))
        layout.addRow("Содержание серы в аноде (%):", self.prebaked_s_input)

        self.prebaked_z_input = QLineEdit()
        self.prebaked_z_input.setValidator(QDoubleValidator(0.0, 100.0, 4, self))
        layout.addRow("Содержание золы в аноде (%):", self.prebaked_z_input)

        return widget

    def _create_coke_calcination_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.coke_calc_consumption_input = QLineEdit()
        self.coke_calc_consumption_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        layout.addRow("Расход сырого кокса (т/год):", self.coke_calc_consumption_input)

        self.coke_loss_factor_input = QLineEdit()
        self.coke_loss_factor_input.setValidator(QDoubleValidator(0.0, 100.0, 4, self))
        layout.addRow("Угар кокса (%):", self.coke_loss_factor_input)

        self.coke_carbon_content_input_calc = QLineEdit("96.0")
        self.coke_carbon_content_input_calc.setValidator(QDoubleValidator(0.0, 100.0, 4, self))
        layout.addRow("Содержание углерода в коксе (%):", self.coke_carbon_content_input_calc)
        
        return widget
        
    def _create_green_anode_baking_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.green_anode_prod_input = QLineEdit()
        self.green_anode_prod_input.setValidator(QDoubleValidator(0.0, 1e9, 6, self))
        layout.addRow("Производство 'зеленых' анодов (т/год):", self.green_anode_prod_input)
        
        return widget

    def _perform_calculation(self):
        try:
            current_index = self.calc_type_combobox.currentIndex()
            result_text = "Результат: "

            if current_index == 0: # ПФУ
                tech = self.pfc_technology_combobox.currentText()
                al_prod = float(self.aluminium_production_input.text().replace(',', '.'))
                aef = float(self.aef_input.text().replace(',', '.'))
                aed = float(self.aed_input.text().replace(',', '.'))
                emissions = self.calculator.calculate_pfc_emissions(tech, al_prod, aef, aed)
                result_text += f"{emissions['cf4']:.4f} т CF4, {emissions['c2f6']:.4f} т C2F6"

            elif current_index == 1: # CO2 Содерберг
                paste = float(self.soderberg_anode_paste_input.text().replace(',', '.'))
                h = float(self.soderberg_h_input.text().replace(',', '.'))
                s = float(self.soderberg_s_input.text().replace(',', '.'))
                z = float(self.soderberg_z_input.text().replace(',', '.'))
                emissions = self.calculator.calculate_soderberg_co2_emissions(paste, h, s, z)
                result_text += f"{emissions:.4f} т CO2/т Ал."

            elif current_index == 2: # CO2 Обожженные аноды
                anode = float(self.prebaked_anode_input.text().replace(',', '.'))
                s = float(self.prebaked_s_input.text().replace(',', '.'))
                z = float(self.prebaked_z_input.text().replace(',', '.'))
                emissions = self.calculator.calculate_prebaked_anode_co2_emissions(anode, s, z)
                result_text += f"{emissions:.4f} т CO2/т Ал."

            elif current_index == 3: # CO2 Прокалка кокса
                consumption = float(self.coke_calc_consumption_input.text().replace(',', '.'))
                loss = float(self.coke_loss_factor_input.text().replace(',', '.'))
                carbon = float(self.coke_carbon_content_input_calc.text().replace(',', '.'))
                emissions = self.calculator.calculate_coke_calcination_co2(consumption, loss, carbon)
                result_text += f"{emissions:.4f} т CO2"

            elif current_index == 4: # CO2 Обжиг "зеленых" анодов
                production = float(self.green_anode_prod_input.text().replace(',', '.'))
                emissions = self.calculator.calculate_green_anode_baking_co2(production)
                result_text += f"{emissions:.4f} т CO2"

            self.result_label.setText(result_text)

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", f"Пожалуйста, проверьте введенные данные. {e}")
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")