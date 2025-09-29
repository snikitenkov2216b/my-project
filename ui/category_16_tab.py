# ui/category_16_tab.py - Виджет вкладки для расчетов по Категории 16.
# Реализует сложный интерфейс для всех процессов производства алюминия.
# Код написан полностью, без сокращений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt, QLocale

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
        self.c_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Выбор процесса ---
        process_layout = QFormLayout()
        self.process_combobox = QComboBox()
        self.process_combobox.addItems([
            "Выбросы ПФУ (CF4, C2F6)",
            "Выбросы CO2 (Электролизеры Содерберга)",
            "Выбросы CO2 (Обожженные аноды)",
            "Выбросы CO2 от прокалки кокса",
            "Выбросы CO2 от обжига 'зеленых' анодов"
        ])
        process_layout.addRow("Выберите тип расчета:", self.process_combobox)
        main_layout.addLayout(process_layout)
        
        # --- Стек виджетов для разных процессов ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_pfc_widget())
        self.stacked_widget.addWidget(self._create_soderberg_widget())
        self.stacked_widget.addWidget(self._create_prebaked_anode_widget())
        self.stacked_widget.addWidget(self._create_coke_calcination_widget())
        self.stacked_widget.addWidget(self._create_green_anode_baking_widget())
        main_layout.addWidget(self.stacked_widget)

        self.process_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
        # --- Кнопка и результат ---
        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_input_field(self, layout, label, validator_params=None):
        """Вспомогательная функция для создания поля ввода с валидатором."""
        line_edit = QLineEdit()
        if validator_params:
            validator = QDoubleValidator(*validator_params, self)
            validator.setLocale(self.c_locale)
            line_edit.setValidator(validator)
        layout.addRow(label, line_edit)
        return line_edit

    def _create_pfc_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.pfc_tech_combobox = QComboBox()
        tech_types = self.data_service.get_aluminium_tech_types_16_1()
        self.pfc_tech_combobox.addItems(tech_types)
        layout.addRow("Технология электролизера:", self.pfc_tech_combobox)

        self.pfc_al_production_input = self._create_input_field(layout, "Производство алюминия (т/год):", (0.0, 1e9, 6))
        self.pfc_aef_input = self._create_input_field(layout, "Частота анодных эффектов (шт./ванно-сутки):", (0.0, 1e9, 6))
        self.pfc_aed_input = self._create_input_field(layout, "Продолжительность анодных эффектов (мин/шт.):", (0.0, 1e9, 6))
        
        return widget

    def _create_soderberg_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.soderberg_paste_input = self._create_input_field(layout, "Расход анодной массы (т/т Al):", (0.0, 1e9, 6))
        self.soderberg_h_input = self._create_input_field(layout, "Содержание водорода (H) в массе (%):", (0.0, 100.0, 4))
        self.soderberg_s_input = self._create_input_field(layout, "Содержание серы (S) в массе (%):", (0.0, 100.0, 4))
        self.soderberg_z_input = self._create_input_field(layout, "Содержание золы (Z) в массе (%):", (0.0, 100.0, 4))
        
        return widget

    def _create_prebaked_anode_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.prebaked_anode_input = self._create_input_field(layout, "Расход обожженных анодов (т/т Al):", (0.0, 1e9, 6))
        self.prebaked_s_input = self._create_input_field(layout, "Содержание серы (S) в аноде (%):", (0.0, 100.0, 4))
        self.prebaked_z_input = self._create_input_field(layout, "Содержание золы (Z) в аноде (%):", (0.0, 100.0, 4))
        
        return widget

    def _create_coke_calcination_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.coke_calc_consumption_input = self._create_input_field(layout, "Расход сырого кокса (т):", (0.0, 1e9, 6))
        self.coke_calc_loss_input = self._create_input_field(layout, "Угар кокса при прокалке (%):", (0.0, 100.0, 4))
        self.coke_calc_carbon_input = self._create_input_field(layout, "Содержание углерода в коксе (%):", (0.0, 100.0, 4))

        return widget

    def _create_green_anode_baking_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.green_anode_prod_input = self._create_input_field(layout, "Производство 'зеленых' анодов (т):", (0.0, 1e9, 6))
        
        return widget

    def _get_float_from_input(self, line_edit, field_name):
        """Получает числовое значение из поля ввода, обрабатывая ошибки."""
        text = line_edit.text().replace(',', '.')
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        try:
            current_process = self.process_combobox.currentIndex()
            result_text = ""

            if current_process == 0:  # ПФУ
                tech = self.pfc_tech_combobox.currentText()
                prod = self._get_float_from_input(self.pfc_al_production_input, "Производство алюминия")
                aef = self._get_float_from_input(self.pfc_aef_input, "Частота анодных эффектов")
                aed = self._get_float_from_input(self.pfc_aed_input, "Продолжительность анодных эффектов")
                
                pfc_emissions = self.calculator.calculate_pfc_emissions(tech, prod, aef, aed)
                result_text = f"Результат: {pfc_emissions['cf4']:.4f} т CF4, {pfc_emissions['c2f6']:.4f} т C2F6"
            
            elif current_process == 1:  # Содерберг
                paste = self._get_float_from_input(self.soderberg_paste_input, "Расход анодной массы")
                h = self._get_float_from_input(self.soderberg_h_input, "Содержание водорода")
                s = self._get_float_from_input(self.soderberg_s_input, "Содержание серы")
                z = self._get_float_from_input(self.soderberg_z_input, "Содержание золы")
                
                # Примечание: UI для детализированных потерь не реализован для простоты.
                # Передаем пустые словари.
                co2_emissions = self.calculator.calculate_soderberg_co2_emissions(paste, h, s, z, {}, {}, {}, {})
                result_text = f"Результат: {co2_emissions:.4f} т CO2 / т Al"

            elif current_process == 2:  # Обожженные аноды
                anode_cons = self._get_float_from_input(self.prebaked_anode_input, "Расход обожженных анодов")
                s_prebaked = self._get_float_from_input(self.prebaked_s_input, "Содержание серы")
                z_prebaked = self._get_float_from_input(self.prebaked_z_input, "Содержание золы")
                
                # Примечание: UI для детализированных потерь не реализован для простоты.
                co2_emissions = self.calculator.calculate_prebaked_anode_co2_emissions(anode_cons, s_prebaked, z_prebaked, {}, {})
                result_text = f"Результат: {co2_emissions:.4f} т CO2 / т Al"

            elif current_process == 3:  # Прокалка кокса
                coke_cons = self._get_float_from_input(self.coke_calc_consumption_input, "Расход сырого кокса")
                loss_factor = self._get_float_from_input(self.coke_calc_loss_input, "Угар кокса")
                carbon_content = self._get_float_from_input(self.coke_calc_carbon_input, "Содержание углерода")
                
                co2_emissions = self.calculator.calculate_coke_calcination_co2(coke_cons, loss_factor, carbon_content)
                result_text = f"Результат: {co2_emissions:.4f} тонн CO2"

            elif current_process == 4:  # Обжиг "зеленых" анодов
                green_anode_prod = self._get_float_from_input(self.green_anode_prod_input, "Производство 'зеленых' анодов")
                
                co2_emissions = self.calculator.calculate_green_anode_baking_co2(green_anode_prod)
                result_text = f"Результат: {co2_emissions:.4f} тонн CO2"

            self.result_label.setText(result_text)

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            self.result_label.setText("Результат: Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")