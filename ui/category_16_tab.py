# ui/category_16_tab.py - Виджет вкладки для расчетов по Категории 16.
# Реализует полный и детализированный интерфейс для всех процессов
# производства алюминия, включая все виды потерь. Без упрощений.
# Комментарии на русском. Поддержка UTF-8.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QStackedWidget, QGroupBox, QScrollArea, QCheckBox
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
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_pfc_widget())
        self.stacked_widget.addWidget(self._create_soderberg_widget())
        self.stacked_widget.addWidget(self._create_prebaked_anode_widget())
        self.stacked_widget.addWidget(self._create_coke_calcination_widget())
        self.stacked_widget.addWidget(self._create_green_anode_baking_widget())
        main_layout.addWidget(self.stacked_widget)

        self.process_combobox.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        
        self.calculate_button = QPushButton("Рассчитать выбросы")
        self.calculate_button.clicked.connect(self._perform_calculation)
        main_layout.addWidget(self.calculate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.result_label = QLabel("Результат:...")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _create_line_edit(self, default_text="", validator_params=None, placeholder=""):
        line_edit = QLineEdit(default_text)
        line_edit.setPlaceholderText(placeholder)
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
        # ИСПРАВЛЕНО: Вызываем новую функцию для получения списка
        self.pfc_tech_combobox.addItems(self.data_service.get_aluminium_tech_types_16_1())
        layout.addRow("Технология электролизера:", self.pfc_tech_combobox)
        self.pfc_al_production_input = self._create_line_edit("", (0.0, 1e9, 6))
        layout.addRow("Производство алюминия (т/год):", self.pfc_al_production_input)
        self.pfc_aef_input = self._create_line_edit("", (0.0, 1e9, 6))
        layout.addRow("Частота анодных эффектов (шт./ванно-сутки):", self.pfc_aef_input)
        self.pfc_aed_input = self._create_line_edit("", (0.0, 1e9, 6))
        layout.addRow("Продолжительность анодных эффектов (мин/шт.):", self.pfc_aed_input)
        return widget

    def _create_soderberg_widget(self):
        scroll, layout = self._create_scrollable_area()

        base_group = QGroupBox("Основные параметры")
        base_layout = QFormLayout(base_group)
        self.soderberg_paste_input = self._create_line_edit("", (0.0, 1e9, 6))
        base_layout.addRow("Расход анодной массы (т/т Al):", self.soderberg_paste_input)
        self.soderberg_h_input = self._create_line_edit("", (0.0, 100.0, 4))
        base_layout.addRow("Содержание водорода (H) в массе (%):", self.soderberg_h_input)
        self.soderberg_s_input = self._create_line_edit("", (0.0, 100.0, 4))
        base_layout.addRow("Содержание серы (S) в массе (%):", self.soderberg_s_input)
        self.soderberg_z_input = self._create_line_edit("", (0.0, 100.0, 4))
        base_layout.addRow("Содержание золы (Z) в массе (%):", self.soderberg_z_input)
        layout.addWidget(base_group)

        # Детализированные потери
        losses_group = QGroupBox("Детализированный расчет потерь углерода (опционально)")
        losses_layout = QVBoxLayout(losses_group)

        # Потери со смолой
        tar_group = QGroupBox("Потери со смолой (ф. 16.9-16.11)")
        tar_layout = QFormLayout(tar_group)
        self.sod_tar_p_sm_r = self._create_line_edit("0.0", (0.0, 1e9, 6))
        tar_layout.addRow("Рециркулируемая смола P_см_r (кг/т Al):", self.sod_tar_p_sm_r)
        self.sod_tar_w_c_sm = self._create_line_edit("0.0", (0.0, 100.0, 4))
        tar_layout.addRow("Содержание C в смоле W_с_см (%):", self.sod_tar_w_c_sm)
        self.sod_tar_eta_k = self._create_line_edit("0.0", (0.0, 1.0, 4))
        tar_layout.addRow("Эффективность улавливания eta_к (доля):", self.sod_tar_eta_k)
        self.sod_tar_p_sm_psh = self._create_line_edit("0.0", (0.0, 1e9, 6))
        tar_layout.addRow("Потери при перестановке штырей P_см_пш (кг/т Al):", self.sod_tar_p_sm_psh)
        self.sod_tar_wet_scrubber = QCheckBox("Используется мокрая газоочистка")
        tar_layout.addRow(self.sod_tar_wet_scrubber)
        losses_layout.addWidget(tar_group)

        # Потери с пылью
        dust_group = QGroupBox("Потери с пылью (ф. 16.12-16.14)")
        dust_layout = QFormLayout(dust_group)
        self.sod_dust_p_pyl_r = self._create_line_edit("0.0", (0.0, 1e9, 6))
        dust_layout.addRow("Рециркулируемая пыль P_пыль_r (кг/т Al):", self.sod_dust_p_pyl_r)
        self.sod_dust_w_c_pyl = self._create_line_edit("0.0", (0.0, 100.0, 4))
        dust_layout.addRow("Содержание C в пыли W_с_пыль (%):", self.sod_dust_w_c_pyl)
        self.sod_dust_eta_k = self._create_line_edit("0.0", (0.0, 1.0, 4))
        dust_layout.addRow("Эффективность улавливания eta_к (доля):", self.sod_dust_eta_k)
        self.sod_dust_wet_scrubber = QCheckBox("Используется мокрая газоочистка")
        dust_layout.addRow(self.sod_dust_wet_scrubber)
        losses_layout.addWidget(dust_group)

        # Потери с пеной
        foam_group = QGroupBox("Потери с пеной (ф. 16.15)")
        foam_layout = QFormLayout(foam_group)
        self.sod_foam_p_pena_vyh = self._create_line_edit("0.0", (0.0, 1e9, 6))
        foam_layout.addRow("Выход пены P_пена_вых (кг/т Al):", self.sod_foam_p_pena_vyh)
        self.sod_foam_w_c_pena = self._create_line_edit("0.0", (0.0, 100.0, 4))
        foam_layout.addRow("Содержание C в пене W_с_пена (%):", self.sod_foam_w_c_pena)
        losses_layout.addWidget(foam_group)

        # Мокрая газоочистка
        scrub_group = QGroupBox("Выбросы от мокрой газоочистки (ф. 16.16)")
        scrub_layout = QFormLayout(scrub_group)
        self.sod_scrub_p_so2 = self._create_line_edit("0.0", (0.0, 1e9, 6))
        scrub_layout.addRow("Масса образовавшегося SO2 (кг/т Al):", self.sod_scrub_p_so2)
        self.sod_scrub_eta_so2 = self._create_line_edit("0.0", (0.0, 1.0, 4))
        scrub_layout.addRow("Эффективность удаления SO2 eta (доля):", self.sod_scrub_eta_so2)
        losses_layout.addWidget(scrub_group)
        
        layout.addWidget(losses_group)
        return scroll

    def _create_prebaked_anode_widget(self):
        scroll, layout = self._create_scrollable_area()

        base_group = QGroupBox("Основные параметры")
        base_layout = QFormLayout(base_group)
        self.prebaked_anode_input = self._create_line_edit("", (0.0, 1e9, 6))
        base_layout.addRow("Расход обожженных анодов (т/т Al):", self.prebaked_anode_input)
        self.prebaked_s_input = self._create_line_edit("", (0.0, 100.0, 4))
        base_layout.addRow("Содержание серы (S) в аноде (%):", self.prebaked_s_input)
        self.prebaked_z_input = self._create_line_edit("", (0.0, 100.0, 4))
        base_layout.addRow("Содержание золы (Z) в аноде (%):", self.prebaked_z_input)
        layout.addWidget(base_group)
        
        losses_group = QGroupBox("Детализированный расчет потерь углерода (опционально)")
        losses_layout = QVBoxLayout(losses_group)

        dust_group = QGroupBox("Потери с пылью (ф. 16.19)")
        dust_layout = QFormLayout(dust_group)
        self.pb_dust_p_pyl_f = self._create_line_edit("0.0", (0.0, 1e9, 6))
        dust_layout.addRow("Фактические выбросы пыли P_пыль_ф (кг/т Al):", self.pb_dust_p_pyl_f)
        self.pb_dust_w_c_pyl = self._create_line_edit("0.0", (0.0, 100.0, 4))
        dust_layout.addRow("Доля С в пыли Д_с_пыль (%):", self.pb_dust_w_c_pyl)
        losses_layout.addWidget(dust_group)
        
        foam_group = QGroupBox("Потери с пеной (ф. 16.20)")
        foam_layout = QFormLayout(foam_group)
        self.pb_foam_p_pena_vyh = self._create_line_edit("0.0", (0.0, 1e9, 6))
        foam_layout.addRow("Выход пены P_пена_вых (кг/т Al):", self.pb_foam_p_pena_vyh)
        self.pb_foam_w_c_pena = self._create_line_edit("0.0", (0.0, 100.0, 4))
        foam_layout.addRow("Доля С в пене Д_с_пена (%):", self.pb_foam_w_c_pena)
        losses_layout.addWidget(foam_group)
        
        layout.addWidget(losses_group)
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
        text = line_edit.text().replace(',', '.')
        if not text:
            raise ValueError(f"Поле '{field_name}' не может быть пустым.")
        return float(text)

    def _perform_calculation(self):
        try:
            current_process = self.process_combobox.currentIndex()
            result_text = ""

            if current_process == 0:
                tech = self.pfc_tech_combobox.currentText()
                prod = self._get_float(self.pfc_al_production_input, "Производство алюминия")
                aef = self._get_float(self.pfc_aef_input, "Частота анодных эффектов")
                aed = self._get_float(self.pfc_aed_input, "Продолжительность анодных эффектов")
                pfc_emissions = self.calculator.calculate_pfc_emissions(tech, prod, aef, aed)
                result_text = f"Результат: {pfc_emissions['cf4']:.4f} т CF4, {pfc_emissions['c2f6']:.4f} т C2F6"
            
            elif current_process == 1:
                paste = self._get_float(self.soderberg_paste_input, "Расход анодной массы")
                h = self._get_float(self.soderberg_h_input, "Содержание водорода")
                s = self._get_float(self.soderberg_s_input, "Содержание серы")
                z = self._get_float(self.soderberg_z_input, "Содержание золы")
                
                tar_params = {
                    'p_sm_r': self._get_float(self.sod_tar_p_sm_r, "Рециркулируемая смола"),
                    'w_c_sm': self._get_float(self.sod_tar_w_c_sm, "Содержание C в смоле"),
                    'eta_k': self._get_float(self.sod_tar_eta_k, "Эффективность улавливания смолы"),
                    'p_sm_psh': self._get_float(self.sod_tar_p_sm_psh, "Потери смолы при перестановке"),
                    'has_wet_scrubber': self.sod_tar_wet_scrubber.isChecked()
                }
                dust_params = {
                    'p_pyl_r': self._get_float(self.sod_dust_p_pyl_r, "Рециркулируемая пыль"),
                    'w_c_pyl': self._get_float(self.sod_dust_w_c_pyl, "Содержание C в пыли"),
                    'eta_k': self._get_float(self.sod_dust_eta_k, "Эффективность улавливания пыли"),
                    'has_wet_scrubber': self.sod_dust_wet_scrubber.isChecked()
                }
                foam_params = {
                    'p_pena_vyh': self._get_float(self.sod_foam_p_pena_vyh, "Выход пены"),
                    'w_c_pena': self._get_float(self.sod_foam_w_c_pena, "Содержание C в пене")
                }
                scrub_params = {
                    'p_so2': self._get_float(self.sod_scrub_p_so2, "Масса SO2"),
                    'eta_so2': self._get_float(self.sod_scrub_eta_so2, "Эффективность удаления SO2")
                }
                
                co2_emissions = self.calculator.calculate_soderberg_co2_emissions(paste, h, s, z, tar_params, dust_params, foam_params, scrub_params)
                result_text = f"Результат: {co2_emissions:.4f} т CO2 / т Al"

            elif current_process == 2:
                anode_cons = self._get_float(self.prebaked_anode_input, "Расход обожженных анодов")
                s_prebaked = self._get_float(self.prebaked_s_input, "Содержание серы")
                z_prebaked = self._get_float(self.prebaked_z_input, "Содержание золы")
                
                dust_params = {
                    'p_pyl_f': self._get_float(self.pb_dust_p_pyl_f, "Фактические выбросы пыли"),
                    'w_c_pyl': self._get_float(self.pb_dust_w_c_pyl, "Доля C в пыли")
                }
                foam_params = {
                    'p_pena_vyh': self._get_float(self.pb_foam_p_pena_vyh, "Выход пены"),
                    'w_c_pena': self._get_float(self.pb_foam_w_c_pena, "Доля C в пене")
                }
                
                co2_emissions = self.calculator.calculate_prebaked_anode_co2_emissions(anode_cons, s_prebaked, z_prebaked, dust_params, foam_params)
                result_text = f"Результат: {co2_emissions:.4f} т CO2 / т Al"

            elif current_process == 3:
                coke_cons = self._get_float(self.coke_calc_consumption_input, "Расход сырого кокса")
                loss_factor = self._get_float(self.coke_calc_loss_input, "Угар кокса")
                carbon_content = self._get_float(self.coke_calc_carbon_input, "Содержание углерода")
                co2_emissions = self.calculator.calculate_coke_calcination_co2(coke_cons, loss_factor, carbon_content)
                result_text = f"Результат: {co2_emissions:.4f} тонн CO2"

            elif current_process == 4:
                green_anode_prod = self._get_float(self.green_anode_prod_input, "Производство 'зеленых' анодов")
                co2_emissions = self.calculator.calculate_green_anode_baking_co2(green_anode_prod)
                result_text = f"Результат: {co2_emissions:.4f} тонн CO2"

            self.result_label.setText(result_text)

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошла непредвиденная ошибка: {e}")
            self.result_label.setText("Результат: Ошибка")